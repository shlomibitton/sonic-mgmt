package com.mellanox.jenkins

def pre(name, ci_tools) {
    return true
}


def run_step(name, ci_tools) {
    def mgmt_tools
    try {
        mgmt_tools = ci_tools.load_project_lib("${env.SHARED_LIB_FILE}")
        env.nfs_dir = "/auto/sw_system_project/devops/sw-r2d2-bot/${env.JOB_NAME}/${currentBuild.number}"

        //copy build moduls dir
        if (!fileExists(env.nfs_dir + "/build")) {
            ci_tools.run_sh("mkdir -p ${env.nfs_dir}/build/ci")
            ci_tools.run_sh("mkdir -p ${env.nfs_dir}/sonic-mgmt")
            ci_tools.run_sh("chmod -R 777 ${env.nfs_dir}")
            ci_tools.run_sh("mkdir -p ${env.nfs_dir}/LOGS")
            ci_tools.run_sh("chmod 777 ${env.nfs_dir}/LOGS")
            print "copying mgmt repo files to " + env."nfs_dir"
            ci_tools.run_sh("cp -rf ./. ${env.nfs_dir}/sonic-mgmt/")
            ci_tools.run_sh("cp -r build/. ${env.nfs_dir}/build/")
            //Copy bat properties from sonic_devops shared location (used by bat.groovy)
            ci_tools.run_sh("cp /auto/sw_system_release/ci/sonic_devops/build/ci/bat_properties_file.txt ${env.nfs_dir}/build/ci/")
        }

        //copy sonic_devops build
        ci_tools.run_sh("mkdir -p ${env.nfs_dir}/sonic_devops/build")
        ci_tools.run_sh("chmod 777 ${env.nfs_dir}/sonic_devops/build")

        def branch_map = ci_tools.read_json(ci_tools.getFileContent("${env.SONIC_BRANCH_MAP}"))
        def sonic_branch = env.GERRIT_BRANCH.replace("develop-", "")
        if (branch_map["${env.GERRIT_BRANCH}"] && ci_tools.is_parameter_contains_value(branch_map["${env.GERRIT_BRANCH}"])) {
            sonic_branch = branch_map["${env.GERRIT_BRANCH}"]
        }
        def lastrc_version = mgmt_tools.get_lastrc_version(ci_tools, sonic_branch)
        def bin_path = "${env.VERSION_DIRECTORY}/${lastrc_version}/Mellanox/sonic-mellanox.bin"
        if (! new File(bin_path).exists()) {
                error "ERROR: bin file not found: ${bin_path}"
        }
        env.BASE_VERSION = bin_path

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
