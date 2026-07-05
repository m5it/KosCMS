#include <iostream>
#include <vector>
#include <string>

#define VERSION "1.0.0"

template<typename T>
class Container {
    std::vector<T> data;
public:
    void add(T item) { data.push_back(item); }
};

int main() {
    std::cout << "C++ Application" << std::endl;
    return 0;
}