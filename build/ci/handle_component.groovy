package com.mellanox.jenkins.generic_modules

def pre(name, ci_tools) {
    return true
}


def run_step(name, ci_tools) {
    try {
        if (env.RUN_COMMUNITY_REGRESSION && env.RUN_COMMUNITY_REGRESSION.toBoolean() == true &&  env.CHANGED_COMPONENTS && env.CHANGED_COMPONENTS.contains("NoMatch")) {
            print "Topic \"RUN_COMMUNITY_REGRESSION=true\" and changed files triggered community regression tests"
        } else {
            env.SKIP_COMMUNITY_REGRESSION = true
            ci_tools.insert_test_result_to_matrix(name, "ETH Community", "SPC", "Skipped=status")

        }
        return true
    }
    catch (Throwable exc) {
        ci_tools.set_error_in_env(exc, "user", name)
        return false

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
