import sys
import constants


def extend_sys_path():
    if constants.VER_SDK_PATH not in sys.path:
        sys.path.append(constants.VER_SDK_PATH)
    for p in constants.EXTRA_PACKAGE_PATH_LIST:
        if p not in sys.path:
            sys.path.append(p)
