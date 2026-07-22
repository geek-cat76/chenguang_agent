# 文件 test_sample.py
def add(x, y):
    return x + y

def test_add():
    assert add(2, 3) == 5

def test_add_fail():
    assert add(2, 2) == 4  # 故意写错的断言，用来演示失败的测试