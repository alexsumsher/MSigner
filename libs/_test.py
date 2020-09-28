from __future__ import print_function
import sys
from wfiles import xltpl

xltpl.workfd='E:\\Alex\\fenlu\\xlsx_tpl'
xltpl.gen_by_xlsx('期末试卷分析导出1.xlsx', True)
# 
# 
def testfun1(n):
	t1 = xltpl('期末试卷分析导出2')
	print(t1.export())
	t_kdata = {
		'title': '南油小学2019——2010学年 年度学期期末考试试卷分析',
		'subject': '语文',
		'teacher': '张老师',
		'classic': '典型题分析：……',
		'totally': '总体来说。。。',
		'problems': '问题在于。。。。',
		'improve': '改进的地方法。。。。。'
	}
	t_rdata = {'row_start': 4, 'col_start': 1, 'rows': [["201901", 40, 40, 4000, 10, 1, 2, 3, 8, '10%', '9%'],["201902", 40, 40, 4000, 10, 1, 2, 3, 8, '10%', '9%']]}
	t1.make_file('testout' + str(n), t_kdata, t_rdata)

def maketpl(tpl_fullpath):
	xltpl.gen_by_xlsx(tpl_fullpath)


if __name__ == '__main__':
	#testfun1(3)
	maketpl(sys.argv[1])
	print("OK")