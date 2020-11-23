package com.mellanox.jenkins

def get_lastrc_version(ci_tools, target_branch) {
    //Check for lastrc
    try {
        def lastrc = ci_tools.run_sh_return_output("readlink ${env.VERSION_DIRECTORY}/${target_branch}-lastrc-internal-sonic-mellanox.bin")
        def lastrc_version = lastrc.replace("${env.VERSION_DIRECTORY}", "").replace("/Mellanox/sonic-mellanox.bin", "").replace("/", "")
        print "CI will use branch:${target_branch} lastrc version: ${lastrc_version} for running BAT"
        return lastrc_version
    } catch (Throwable lastrc_ex) {
        //Handle non exist links
        error "No lastrc soft link is available for branch ${target_branch}. please contact DevOps for more help"
    }
}

return this