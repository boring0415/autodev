#include <cassert>
#include <iostream>
#include <numeric>
#include <vector>

double calculate_average(const std::vector<int>& values) {
    if (values.empty()) return 0.0;
    return std::accumulate(values.begin(), values.end(), 0) / values.size();
}

int main() {
    const double actual = calculate_average({1, 2});
    if (actual != 1.5) {
        std::cerr << "expected 1.5, got " << actual << "\n";
        return 1;
    }
    return 0;
}
