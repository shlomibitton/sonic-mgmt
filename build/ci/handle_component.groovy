package com.mellanox.jenkins.generic_modules

def pre(name, ci_tools) {
    return true
}


def run_step(name, ci_tools) {
    try {
        if (env.RUN_REGRESSION && env.RUN_REGRESSION.toBoolean() == true) {
            print "Regression test are defined to run with topic \"RUN_REGRESSION=true\""
        } else if (env.CHANGED_COMPONENTS && env.CHANGED_COMPONENTS.contains("NoMatch")) {
            print "Changed files triggered regression tests"
        } else {
            env.SKIP_MINI_REGRESSION = true
        }
        return true
    }
    catch (Throwable exc) {
        ci_tools.set_error_in_env(exc, "user", name)
        return false

    }
    finally {
        if (env.SKIP_MINI_REGRESSION == "true") {
//            ci_tools.insert_test_result_to_matrix(name, "IB", "SIB2", "Skipped=status")
        }
    }
}


def post(name, ci_tools) {
    return true
}


def cleanup(name, ci_tools) {
    return true
}

def headline(name) {
    return "${name} " + env."${name}_status"
}


def summary(name) {
    if (env."${name}_status" != "Success") {
        return env."${name}_status" + " - exception: " + env."${name}_error"
    } else {
        return env."${name}_status"
    }
}


return this
