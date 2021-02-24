package com.mellanox.jenkins

def get_lastrc_version(ci_tools, target_branch) {
    //Check for lastrc
    try {
        def version_path = env.VERSION_DIRECTORY
        def lastrc = ci_tools.run_sh_return_output("readlink ${version_path}/${target_branch}-lastrc-internal-sonic-mellanox.bin")
        if (lastrc.contains("_Public")) {
            version_path = version_path  + "/public"
        }
        def lastrc_version = lastrc.replace("${version_path}", "").replace("/Mellanox/sonic-mellanox.bin", "").replace("/", "")
        print "CI will use branch:${target_branch} lastrc version: ${lastrc_version} for running BAT"
        return lastrc_version
    } catch (Throwable lastrc_ex) {
        //Handle non exist links
        error "No lastrc soft link is available for branch ${target_branch}. please contact DevOps for more help"
    }
}

return this