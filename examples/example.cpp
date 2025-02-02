#include <iostream>
using namespace std;

// This is a free function
int add(int a, int b)
{
    return a + b;
}

class MyClass {
public:
    MyClass(int x): val(x) {}

    // This is a method
    int getValue() {
        return val;
    }

    // Another method calling add
    int doAdd(int y) {
        return add(val, y);
    }

private:
    int val;
};

int main() {
    MyClass obj(5);
    cout << obj.getValue() << endl;
    cout << obj.doAdd(3) << endl;
    return 0;
}
