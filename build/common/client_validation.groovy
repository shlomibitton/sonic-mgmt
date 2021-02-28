import groovy.json.JsonSlurperClassic

htmlHeadStart = "<head><style>"
htmlHeadEnd = "th.chips, td.chips{  border-left: 1px solid black;border-right: 1px solid black} td.chips_bottom, " +
        "th{  border-left: 1px solid black;border-right: 1px solid black; border-bottom: 1px solid black}</style></head>" +
        "<body></B>"
htmlHead = htmlHeadStart + htmlHeadEnd

htmlEnd = "</body></html>"

def setError(String error) {
    htmlHead = htmlHeadStart + "button{  visibility: hidden; } " + htmlHeadEnd
    if (!htmlEnd.contains("Error"))
        htmlEnd = "<BR><span  style='color:red'>Error found - please fix</span>" + htmlEnd
    return "<span  style='color:red'>Invalid !!! - ${error}</span>"
}

def assertVariable(var, error) {
    if (var.toLowerCase() != "none" && var != "" && error.size() > 0)
        return true
    else
        return false
}

def set_error_if_empty(current_error, new_error) {
    if (is_parameter_contains_value(current_error))
        return current_error
    else return new_error
}

def readFileMaster(file_path) {
    def newFile = new File(file_path)
    if (newFile.exists()) {
        return newFile.text
    }
    return null
}

def is_folder_exists(folder) {
    folder = new File("${folder}")
    return folder.exists()

}

def read_json(json_text, printException = true) {
    def json_data = null

    try {
        json_data = new JsonSlurperClassic().parseText(json_text)
    }
    catch (Throwable json_ex) {
        if (printException) {
            print(json_ex.toString())
            error "JSON format invalid"
        }
        error ""
    }

    return json_data
}

def is_parameter_contains_value(param) {
    try {
        if (param != "" && param != null) return true
        else return false
    } catch (Throwable exc) {
        return false
    }
}

def mgmt_merge_flow() {
    def erros_map = [:]
    try {
        MGMT_GITHUB_BRANCH = MGMT_GITHUB_BRANCH.trim()
        MGMT_GERRIT_BRANCH = MGMT_GERRIT_BRANCH.trim()
        IMAGE_VERSION = IMAGE_VERSION.trim()
        IMAGE_GITHUB_BRANCH = IMAGE_GITHUB_BRANCH.trim()
        RUN_COMMUNITY_REGRESSION = RUN_COMMUNITY_REGRESSION.trim()

        //Validate branch is defined
        if (!is_parameter_contains_value(MGMT_GITHUB_BRANCH)) {
            erros_map["MGMT_GITHUB_BRANCH"] = set_error_if_empty(erros_map["MGMT_GITHUB_BRANCH"], setError("MGMT_GITHUB_BRANCH is not defined"))
        }

        //Validate branch is defined
        if (!is_parameter_contains_value(MGMT_GERRIT_BRANCH)) {
            erros_map["MGMT_GERRIT_BRANCH"] = set_error_if_empty(erros_map["MGMT_GERRIT_BRANCH"], setError("MGMT_GERRIT_BRANCH is not defined"))
        }

        //Validate image version or image branch are not set together
        if (is_parameter_contains_value(IMAGE_GITHUB_BRANCH) && is_parameter_contains_value(IMAGE_VERSION)) {
            erros_map["IMAGE_GITHUB_BRANCH"] = set_error_if_empty(erros_map["IMAGE_GITHUB_BRANCH"], setError("Please define IMAGE_GITHUB_BRANCH or IMAGE_VERSION."))
            erros_map["IMAGE_VERSION"] = set_error_if_empty(erros_map["IMAGE_VERSION"], setError("Please define IMAGE_GITHUB_BRANCH or IMAGE_VERSION."))
        } else {
            if (is_parameter_contains_value(IMAGE_VERSION)) {
                def bin_path = "/auto/sw_system_release/sonic/"
                if (IMAGE_VERSION.contains("Public")) {
                    bin_path += "/public/"
                }
                bin_path += IMAGE_VERSION + "/Mellanox/sonic-mellanox.bin"
                if (! new File(bin_path).exists()) {
                    erros_map["IMAGE_VERSION"] = set_error_if_empty(erros_map["IMAGE_VERSION"], setError("Path: ${bin_path} does not exist!"))
                }
            }
        }



    } catch (Throwable exc) {
        return exc
    }

    ////return errors_map
    if (RELEASE_ERRORS_MAP && RELEASE_ERRORS_MAP.toBoolean() == true) {
        return erros_map
    }

    def htmlAll = "${htmlHead}"
    def list_of_params = ["MGMT_GITHUB_BRANCH"   : "${MGMT_GITHUB_BRANCH}", "MGMT_GERRIT_BRANCH": "${MGMT_GERRIT_BRANCH}",
                          "IMAGE_VERSION" : "${IMAGE_VERSION}", "IMAGE_GITHUB_BRANCH":"${IMAGE_GITHUB_BRANCH}",
                          "RUN_COMMUNITY_REGRESSION": "${RUN_COMMUNITY_REGRESSION}"]
    list_of_params.each { param, value ->
        htmlAll += "<BR><BR><B>${param}</B></br> &nbsp&nbsp&nbsp${value}</B>"
        if (is_parameter_contains_value(erros_map["${param}"])) {
            htmlAll += "  ${erros_map["${param}"]}"
        }
    }
    htmlAll += "</P>" + htmlEnd
    return htmlAll
}

//Start validation
MGMT_GITHUB_BRANCH = MGMT_GITHUB_BRANCH.replaceAll("origin\\/", "").replaceAll("origin1\\/", "").trim()
MGMT_GERRIT_BRANCH = MGMT_GERRIT_BRANCH.replaceAll("origin\\/", "").replaceAll("origin1\\/", "").trim()

if (MERGE_HTML_VALIDATION && MERGE_HTML_VALIDATION.toBoolean() == true) {
    //Run MERGE_HTML_VALIDATION
    return mgmt_merge_flow()
} else {
    //For build usage
    return this
}