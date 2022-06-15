该项目为一个生成动画的语言。

为使用该项目，需要在pip里安装`requirements.txt`中的依赖：
```
pip install -r requirements.txt
```

随后，可以使用`python3`运行`main.py`，并使用`--input`参数指定输入文件，`--output`参数指定输出文件。
如果使用`--print-type`参数，则会在生成输出文件前，打印其中变量的类型。
例如：
```
python3 main.py --input demo.txt --output demo.svg --print-type
```

可以在浏览器中打开`demo.svg`，查看生成的动画。