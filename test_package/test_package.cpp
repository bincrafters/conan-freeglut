#include <cstdlib>
#include <cstdarg> /* This declares the va_list type */
#include <iostream>

#include "GL/freeglut.h"


void error_handler(const char *fmt, va_list ap) {
    std::cout << fmt << std::endl;
}

int main(int argc, char **argv) {
    glutInitErrorFunc(error_handler);
    // glutInit(&argc, argv);
    std::cout << std::endl << "FreeGLUT version:" << std::endl;
    std::cout << glutGet(GLUT_VERSION);
    std::cout << std::endl;
    return EXIT_SUCCESS;
}
