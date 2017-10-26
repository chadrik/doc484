import sys
import lib2to3.main


def main(args=None):
    sys.exit(lib2to3.main.main("doc484.fixes", args=args))


if __name__ == '__main__':
    main()
