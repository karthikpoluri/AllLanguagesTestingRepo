#include <stdio.h>

// This function prints a greeting
void greet(const char* name) {
    printf(\"Hello, %s!\\n\", name);
}

int main() {
    greet(\"World\");
    return 0;
}
