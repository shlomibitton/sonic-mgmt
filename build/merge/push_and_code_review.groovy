package com.mellanox.jenkins.generic_modules

def param_contain_value(ci_tools, param) {
    if (ci_tools.is_parameter_contains_value(param) && param.toLowerCase() != "none") {
        return true
    } else {
        return false
    }
}

def pre(name, ci_tools)
{
    return true
}


def run_step(name, ci_tools)
{
    try
    {
        //get git branch
        def git_branch = ci_tools.run_sh_return_output("git rev-parse --abbrev-ref HEAD").trim()

        //only trigger formal
        if (env.NEW_CHANGES) {
            //push to gerrit and get commits url's
            print "Pushing commit/s to gerrit"
            def push_output = ci_tools.run_sh_return_output("git push origin ${git_branch}:refs/for/${git_branch}")


            //loop over push string for getting gerrit url's
            def change_number_list = []
            def change_number
            push_output.readLines().each { def line ->
                if (line.contains("http")) {
                    line.split(" ").each { split_str ->
                        if (split_str.contains("http")) {
                            int i = split_str.lastIndexOf("/")
                            change_number = split_str.substring(i).substring(1)
                            change_number_list.add(change_number)
                        }
                    }

                }
            }
            env.MAIL_SUBJECT = "New changes pushed to Gerrit: ${env.GERRIT_HTTP_URL}/${change_number_list.last()}"
            currentBuild.description = env.MAIL_SUBJECT

            def last_commit_str = "Merge from GitHub"

            def commits_pushed = "<tr><td><b>${env.GERRIT_HTTP_URL}/${change_number_list.last()} - ${last_commit_str}</b></td></tr>"

            //loop over all changes except the last one
            for (int i = 0; i < change_number_list.size() - 1; i++) {

                //change topic
                GerritTools.set_topic(ci_tools, change_number_list[i], "IGNORE")

                //set code review +2
                GerritTools.set_score(ci_tools, 'Code-Review', change_number_list[i], 1, '+2')

                commits_pushed += "<tr><td>${env.GERRIT_HTTP_URL}/${change_number_list[i]} - IGNORE CI</td></tr>"
            }


            //update last commit
            //add build name and number
            def topic = "${JOB_BASE_NAME} #${BUILD_NUMBER}"

            def possible_topic_list = ["RUN_COMMUNITY_REGRESSION", "IMAGE_VERSION", "IMAGE_BRANCH"]

            possible_topic_list.each { possible_topic ->
                if (param_contain_value(ci_tools, env."${possible_topic}")) {
                    topic += "," + "${possible_topic}=" + env."${possible_topic}".trim()
                }
            }

            //change topic
            GerritTools.set_topic(ci_tools, change_number_list.last(), "${topic}")

            //set code review +2
            GerritTools.set_score(ci_tools, 'Code-Review', change_number_list.last(), 1, '+2')


            //commits pushed table
            String commits_pushed_html = """ 
            <table class="section">
            <tr class="tr-title">
            <td class="td-title-main" colspan=2>
            COMMITS PUSHED
            </td>
            </tr>
            ${commits_pushed}
            </table>
            </br>
            """

            env.on_the_fly_banners = commits_pushed_html
        }

        return true
    }
    catch (Throwable exc)
    {
        ci_tools.set_error_in_env(exc,"devops",name)
        return false

    }
}



def cleanup(name, ci_tools)
{
    return true
}

def headline(name)
{
    if ("${name}".contains(":")) {
        return "${name}".split(":")[0] + " " + env."${name}_status"
    } else {
        return "${name} " + env."${name}_status"
    }
}


def summary(name)
{
    if (env."${name}_status"!="Success")
    {
        return env."${name}_status" + " - exception: " + env."${name}_error"
    }
    else
    {
        return env."${name}_status"
    }
}


return this
