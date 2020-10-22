<template>
  <div von-tpicker class="von-datepicker" :class="{'active': state == 1}">
    <div class="dp-header">
      <button class="button button-clear button-stable" @click="cancel()">
        <slot name="cancel">
          取消
        </slot>
      </button>

      <button class="button button-clear button-balanced btn-confirm" @click="confirm()">
        <slot name="confirm">
          确定
        </slot>
      </button>
    </div>

    <div class="dp-body">
      <!-- hour -->
      <scroller class="dp-list dp-hour"
        ref="y_scroller"
        :animate-duration="1"
        width="34%"
      >
        <div class="dp-item" v-for="(y, index) in hours" v-text="h"></div>
      </scroller>

      <!-- minutes -->
      <scroller class="dp-list dp-minutes"
        ref="m_scroller"
        :animate-duration="1"
        width="33%"
      >
        <div class="dp-item" v-for="(m, index) in minutes" v-text="m"></div>
      </scroller>

    </div>
  </div>
</template>
<script>
  import channel from './channel'
  const defaultHours = () => [
    '00','01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12','13','14','15','16','17','18','19','20','21','22','23'
  ]
  const defaultMinutes = () => [
    let allminutes = ['00','01','02','03','04','05','06','07','08','09']
		for(let i=10;i<60;i++){
			allminutes.push(i.toString());
		}
		return allminutes;
  ]
  const item_height = 34
  const setOpacity = (el, index) => {
    let dp_items = el.querySelectorAll('.dp-item')
    for (let i = 0; i < dp_items.length; i++) {
      let e = dp_items[i]
      if (i == index) {
        e.style.opacity = '1'
      } else if (Math.abs(i - index) == 1) {
        e.style.opacity = '0.4'
      } else if (Math.abs(i - index) == 2) {
        e.style.opacity = '0.2'
      } else if (Math.abs(i - index) >= 3) {
        e.style.opacity = '0.1'
      }
    }
  }
  export default {
    data() {
      return {
        state: 0, // 0: hide, 1: show
        value: '',
        hours: defaultYears(),
        minutes: defaultMonths(),
      }
    },
    mounted() {
      this.timer = setInterval(() => {
        this.updateHm()
      }, 50)
      channel.$on('PickerCancelEvent', () => {
        this.hide()
      })
    },
    beforeDestroy() {
      if (this.timer)
        clearInterval(this.timer)
    },
    destroyed() {
      document.body.removeChild(document.querySelector('[von-tpicker]'))
    },
    methods: {
      show() {
        $backdrop.show().then(() => {
          let backdrop = document.querySelector('[von-backdrop]')
          backdrop.onclick = () => {
            channel.$emit('PickerCancelEvent')
            backdrop.onclick = null
          }
        })
        setTimeout(() => {
          this.state = 1
          this.$refs.h_scroller.resize()
          this.$refs.m_scroller.resize()
          this.setHm()
        })
      },
      hide() {
        this.state = 0
        $backdrop.hide()
        setTimeout(() => {
          this.$destroy()
        }, 300)
      },
      confirm() {
        channel.$emit('PickerOkEvent', this.value)
      },
      cancel() {
        channel.$emit('PickerCancelEvent')
      },
      updateHm() {
        let hPosition = this.$refs.h_scroller.getPosition()
        let hIndex = parseInt(yPosition.top / item_height) + 3
        let mPosition = this.$refs.m_scroller.getPosition()
        let mIndex = parseInt(mPosition.top / item_height) + 3
        setOpacity(this.$refs.h_scroller.$el, yIndex)
        setOpacity(this.$refs.m_scroller.$el, mIndex)
        let hh = this.hours[hIndex]
        let mm = this.minutes[mIndex]
        this.value = this.hours[yIndex] + ':' + this.minutes[mIndex]
      },
      setHm() {
        let hm = this.value.split(':')
        let hIndex = this.hours.indexOf(hm[0])
        let mIndex = this.minutes.indexOf(hm[1])
        this.$refs.h_scroller.scrollTo(0, item_height * (hIndex - 3))
        this.$refs.m_scroller.scrollTo(0, item_height * (mIndex - 3))
      }
    }
  }
</script>