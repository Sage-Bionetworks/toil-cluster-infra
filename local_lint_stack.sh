# Cloudformation does not allow provisioning stacks with duplicate names.
# This script helps ensure that stack names for newly provisioned
# resources are unique.
#!/bin/bash
set -e
set -o pipefail
set -x

# Name can only contain alpha, number or hyphens, 1st char must be alpha.
# TODO - need to add the following constraints:
#   cannot contain square bracket characters
#   string length must be less than 128 characters
STACK_NAME_CONSTRAINT="^[a-zA-Z][a-zA-Z0-9.-][^_~\`/{},.\"()\"+=\\<>?:;|!@#$%^&*[:space:]]*$"

# util to print a generic list
print_list() {
  local list=("$@")
  for item in "${list[@]}"
  do
    printf "${item}\n"
  done
}

# Get existing stack names from local files
get_local_stack_names() {
  stack_names=( $(/usr/bin/grep -r -w -h 'stack_name:' ${PATH} | /usr/bin/cut -d':' -f2 | /usr/bin/awk '{$1=$1};1') )
}

# Get existing stack names from cloudformation
get_cf_stack_names() {
  stack_names=( $(aws cloudformation list-stacks \
      --query 'StackSummaries[?starts_with(StackStatus, `DELETE_COMPLETE`) != `true`].StackName' \
      --output text) )
}

# Get the newly added stack_name
get_new_stack_name() {
  local diff_output=$(/usr/bin/git diff HEAD~1 | /usr/bin/grep '+stack_name:')
  new_stack_name=${diff_output:13}
}

# Verify new stack_name is unique
verify_unique() {
  for stack_name in "${stack_names[@]}"
  do
    if [ "${new_stack_name}" = "${stack_name}" ]; then
      printf "\e[1;31mERROR: new stack_name \"${new_stack_name}\" is not unique\e[0m\n"
      printf "Existing stacks names:\n"
      print_list "${stack_names[@]}"
      exit 1
     fi
  done
}

# Verify that new stack_name contains valid chars and is a certain length
verify_name_constraint() {
  if [[ ! $new_stack_name =~ $STACK_NAME_CONSTRAINT ]]; then
    printf "\e[1;31mERROR: Stack name \"${new_stack_name}\" contains invalid characters. "
    printf "A stack name can contain only alphanumeric characters (case sensitive) and hyphens. "
    printf "It must start with an alphabetic character and cannot be longer than 128 characters.\e[0m\n"
    exit 1
  fi
}

# Get the list of new or changed files
get_diff_files() {
  local diff_output=$(/usr/bin/git diff --name-only HEAD~1 || true)
  files=($diff_output)
}

# Verify sceptre files are valid
verify_sceptre_files() {
  for file in "${files[@]}"
  do
    # sceptre files are in the config folder
    if [[ "$file" =~ "config" ]]; then
      if [[ $file != *.yaml && $file != *.j2 && $file != *.json ]]; then
        printf "\e[1;31mERROR: \"${file}\" is an invalid template file.  "
        printf "A valid file must contain either a json, yaml or j2 extension\e[0m\n"
        exit 1
      fi
    fi
  done
}

# main
cmd(){ echo `basename $0`; }
usage() {                                      # Function: Print a help message.
echo "\
usage: `cmd` [ -r ] [ -l PATH ]
-r Verify against cloudformation
-l Verify against local files in PATH
"
}

exit_abnormal() {                              # Function: Exit with error.
  usage
  exit 1
}

if [ $# -eq 0 ]; then                          # Requires at least one argument
    exit_abnormal
fi

while getopts ":rl:" options; do
  case "${options}" in
    r) get_new_stack_name
       if [ ! -z "${new_stack_name}" ]; then
         verify_name_constraint
         get_cf_stack_names
         verify_unique
       fi
      ;;
    l) PATH=${OPTARG}
       # verify sceptre files
       get_diff_files
       verify_sceptre_files
       # verify stack names
       get_new_stack_name
       if [ ! -z "${new_stack_name}" ]; then
         verify_name_constraint
         # get all stack names from the last commit
         ( /usr/bin/git checkout HEAD~1 ) 2> /dev/null
         get_local_stack_names
         ( /usr/bin/git checkout - ) 2> /dev/null
         verify_unique
       fi
      ;;
    :)                            # If expected argument omitted:
      printf "\e[1;31mError: -${OPTARG} requires an argument.\e[0m\n"
      exit_abnormal
      ;;
    *)                            # If unknown (any other) option:
      exit_abnormal
      ;;
  esac
done
