package com.mellanox.jenkins

def pre(name, ci_tools) {
    return true
}


def run_step(name, ci_tools) {
    def mgmt_tools
    try {
        //last sha1 from local
        def last_local_commit = ci_tools.run_sh_return_output("git rev-parse ${env.MGMT_GERRIT_BRANCH}").trim()

        //copy commit msg
        if (!fileExists(".git/hooks/commit-msg")) {
            ci_tools.run_sh('''scp -p -P 29418 10.7.77.140:hooks/commit-msg ".git/hooks/"''')
        }
        mgmt_tools = ci_tools.load_project_lib("${env.SHARED_LIB_FILE}")
        ci_tools.run_sh("git remote add upstream ${env.GITHUB_REPOSITORY} && git fetch upstream")
        ci_tools.run_sh("git merge upstream/${env.GITHUB_BRANCH}")
        //Check if there are new changes

        def new_commit = ci_tools.run_sh_return_output("git rev-parse ${env.MGMT_GERRIT_BRANCH}").trim()
        if (new_commit == last_local_commit) {
            env.MAIL_SUBJECT = "There are no new changes available."
            currentBuild.description = env.MAIL_SUBJECT
            print "There are no new changes."
            return true
        }

        //Add changeID
        ci_tools.run_sh("git commit -C HEAD --amend")

        env.NEW_CHANGES = true

        print "New changes found!"

    } catch (Throwable ex) {
        ci_tools.set_error_in_env(ex, "devops", name)
        return false
    }
    return true
}


def cleanup(name, ci_tools) {
    return true
}

def headline(name) {
    if ("${name}".contains(":")) {
        return "${name}".split(":")[0] + " " + env."${name}_status"
    } else {
        return "${name} " + env."${name}_status"
    }
}


def summary(name) {
    if (env."${name}_status" != "Success") {
        return env."${name}_status" + " - exception: " + env."${name}_error"
    } else {
        return env."${name}_status"
    }
}


return this
