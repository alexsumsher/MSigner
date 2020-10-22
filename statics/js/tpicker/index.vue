<template>
  <div von-tpicker class="item item-borderless item-input" @click="showPicker()">
    <span v-if="label != ''" class="input-label" v-text="label"></span>
    <input ref="time" type="time" :value="v">

    <span v-text="formatedDate"></span>

    <div class="hairline-top"></div>
    <div class="hairline-bottom"></div>
  </div>
</template>
<script>
  import Vue from 'vue'
  import tpicker from './tpicker.vue'
  import channel from './channel'
	
  export default {
    props: {
      label: {
        type: String,
        default: ''
      },
      placeholder: {
        type: String,
        default: ''
      },
      value: {
        type: String,
        default: ''
      },
    },
    computed: {
      v: function () {
        return this.value
      }
    },
    data() {
      return {
        picker: undefined, // picker vm
      }
    },
    mounted() {
    },
    methods: {
      showPicker() {
        let el = document.createElement('div')
        el.setAttribute('von-tpicker', '')
        document.body.appendChild(el)
        let PickerComponent = Vue.extend(Picker)
        this.picker = new PickerComponent({
          data: {
            value: this.v
          }
        }).$mount('[von-tpicker]')
        channel.$on('PickerOkEvent', (value) => {
          this.v = value
          console.log('datetime input =>', this.$refs.time)
          this.$refs.time.value = value
          this.$emit('input', value)
          if (this.picker)
            this.picker.hide()
          channel.$off('PickerOkEvent')
        })
        this.picker.show()
      }
    }
  }
</script>