��    �        �         �
     �
     �
     �
                /     A     S     k  	   w  	   �     �     �     �     �     �  "   �          '     ;     J     `     x     �     �     �     �     �     �     �          .     C     T     a     q          �     �     �     �     �     �     �     
          $     7     M     ^     k     y     �     �     �     �     �     �     �               /     F     W     j     z     �     �     �     �     �     �     �            	   %     /     ?     W     g     u     �     �     �     �     �     �     �     �  
             $     3     D     X     f     |     �     �  
   �     �     �     �     �          #     8     M     f     {     �      �     �     �     �     �          *     A     N     e     �     �     �     �     �     �  z  �     l  M   �  "   �  !   �  !        @  %   [  V   �     �     �  N  	     X  %   u     �  5   �  +   �  �     *   �     �  ?  �  b   (  6   �     �     �  (   �  +   '  7   S     �  J   �  �   �     �      �      �   
   !     !     1!     D!     P!     f!     w!     �!     �!     �!     �!     �!  	   �!     �!     �!     	"     "      "     ,"     A"     Q"     c"     q"     �"     �"     �"     �"     �"     �"     �"     �"  	   #     #     #     1#     9#  K   K#     �#     �#  3   �#  2   �#  4   $  I  G$  ;   �*     �*  {  �*  �   f,  �   R-  !   �-     .     .     6.  Z  ;.  	   �1     �1  Q  �1  �  3  +   �5  7   �5     6  +   46  �   `6     7  '   !7     I7  �   N7  �  �7  H   y9     �9     �9  w   �9     b:  %   {:  [   �:  4   �:  4   2;  3   g;  	  �;  0   �D  %   �D  /   E  &   <E  ]   cE  W   �E  *   F  �  DF  8   DL  ,   }L     �L     �L  �  �L  N   �O  6   �O  $   %P     q   w   I   D      S   M   J   c   "           i   @   '   u           Y   R          $       �   =                ,       6   )   A   s   5                     z          P          d   }   Z      K   ^      1       /           y       -   
   7   ]   2          B          g      W   %   9       :   {   a   X   \      x   H   o           v   [      O   |       f   t      *      N          +   L   b       &      e   (   >   #      j   r                             n   G       ;   ~       0   4   8       `   C   h       _   F   ?                <   3               	   !      m           T   E       p          l      .   Q               k       U   V    app_allappstatus_title app_app_param_title app_no_published_app app_nojob_data app_socket_err app_specify_jobid app_specify_param app_subcmd_notsupported app_timeout app_title app_usage cannot_openfile connect_ws_err copying_serverfile dirpermission_denied downalodfile_errnopermission downalodfile_nopermission_notfound download_dirnotexist download_specify_id download_usage downloadfailed_2gb_ws downloadfailed_notfound downloading_file empty_username_err failed_connect_wsurl failed_connws_logon failed_connws_submit failed_to_readfile file_nojob_param https_certificate_missing internal_server_error job_info_app_profile job_info_apptype job_info_cmd job_info_curdir job_info_desc job_info_endtime job_info_est_runtime job_info_exe_cwd job_info_exeutionhost job_info_exitcode job_info_exstatus job_info_fwd job_info_gid job_info_gjob job_info_id job_info_inputfile job_info_localcluster job_info_localid job_info_mem job_info_name job_info_numthread job_info_outfile job_info_pending_reason job_info_pid job_info_priority job_info_projname job_info_queue job_info_remotecluster job_info_remoteid job_info_reqhost job_info_reqprocessors job_info_runtime job_info_starttime job_info_status job_info_submithost job_info_submittime job_info_swap job_info_timeremain job_info_title job_info_type job_info_user job_nomatch_group job_nomatch_name job_nomatch_status job_usage job_usage_error jobaction_specify_jobid jobaction_usage jobdata_usage logon_null_url logon_pac_as logon_specify_password logon_specify_username logon_url_prompt logon_usage logon_username logout_success logout_usage main_usage memory_not_enough must_logon_pac no_service_found notenoughmem_upload pacinfo_usage password_cannot_empty permission_denied_writefile ping_url ping_urlformat_example ping_usage published_app_notfound start_download start_uploading submit_arg_missing submit_cannot_openfile submit_file_notexist submit_input_invalid submit_inputfile_missing submit_param_missing submit_success submit_usage submitjob_failed_filedirnotfound upload_file_notfound upload_fileread_denied upload_jobid_invalid upload_specify_absolutepath upload_specify_jobid upload_specify_srcfile upload_usage uploadfailed_connectws uploading_file_currentjobdir uploading_file_jobdir uploading_inputfile usercmd_usage wrong_inputfile_param wrong_url_format ws_notready_url Project-Id-Version: PACKAGE VERSION
Report-Msgid-Bugs-To: 
POT-Creation-Date: 2014-08-04 15:22+0800
PO-Revision-Date: 2014-08-04 15:26+0800
Last-Translator: root <root@crtvm0049.tw.ibm.com>
Language-Team: English <en@translate.freefriends.org>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8

Content-Transfer-Encoding: 8bit
Plural-Forms: nplurals=2; plural=(n != 1);
 APPLICATION NAME        STATUS ID                LABEL                              MANDATORY  DEFAULT VALUE There are no published application There are no job data for job {0} There was some other socket error Please specify the job id. Please specify the proper parameters. This subcommand is not supported: %s.  To view the command usage, run pacclient help.  There was a timeout HOSTNAME            JOB DATA pacclient.py app usage:

pacclient.py app [--help|-h] [--list|-l] | [--param|-p app_name[:template_name]]

List applications or parameters of an application.

For example, to list all the parameters and default values for an application:
pacclient.py app -p FLUENT

[--param|-p app_name[:template_name]]
	List all parameters and default values for an application. To see parameter values saved in your customized application, specify both the published form name and the custom template name.
[--list|-l]
	Lists all applications and application status
[--help|-h]
	Display subcommand usage. Can not open file '{0}' {1}. Cannot connect to the web service: %s Copying server file: %s You do not have write permission on the directory: %s Download failed. you have no permission: %s Download %s failed. 
	- You have no permission or the specified file does not exist. 
	  Or the parameter of compression command is invalid. 
 The specified directory does not exist: %s Please specify a job ID. pacclient.py download usage:

pacclient.py download [--help|-h] [--dir|-d directory] [--file|-f file_names] [--cmd|-c compression_cmd] job_ID

Download job data for a job.

For example:
pacclient.py download 54321

By default, copy all job data files to the current working directory.

[--dir|-d directory]
	Copy files to the specified directory.
[--file|-f file_names]
	Download the specified files. File name can include wild cards. If specify multiple files, use comma as separator. If there are empty spaces or wild cards in "file_names", it must be enclosed with double-quotes.
	Examples:
	-f "jobfile_*"
	-f jobfile_1,jobfile_2,jobfile_3
	-f "jobfile_*,test 1.txt, test 2.txt"
[--cmd|-c compression_command]
	Download files with specified compression stream.
job_ID
	Specify the job ID.
[--help|-h]
	Display subcommand usage. Unable to download file. Files that are 2 GB or larger cannot be downloaded using Web Services: %s Download failed. The specified file does not exist: %s Downloading file: {0} to {1} Empty username, can not logon. Failed to connect to web service URL: %s Failed to connect to web service and logon. Failed to connect to web service and submission failed. Failed to read from file %s The file does not contain any job parameters. The job cannot be submitted. The https certificate 'cacert.pem' is missing. Copy the 'cacert.pem' file from the GUI_CONFDIR/https/cacert.pem on the IBM Spectrum LSF Application Center to the same directory you are invoking the client program from. Internal server error. Application Profile:%s Application Type:%s Command:%s Current Working Dir:%s Job Description:%s End Time:%s Estimated Run Time:%s Execution CWD:%s Execution Hosts:%s Exit Code:%s External Status:%s Job Forwarding:%s Process Group ID:%s Graphic Job:%s Job ID:%s Input Files:%s Local Cluster:%s Local Job ID:%s Mem:%s Job Name:%s Number Of Threads:%s Output Files:%s Pending Reason:%s Process ID:%s Job Priority:%s Project Name:%s Queue:%s Remote Cluster:%s Remote Job ID:%s Requested Hosts:%s Required Processors:%s Run Time:%s Start Time:%s Status:%s Submission Host:%s Submission Time:%s Swap:%s Time Remaining:%s JOBID     STATUS    EXTERNAL_STATUS        JOB_NAME                 COMMAND Job Type:%s User:%s There are no jobs matching the query: job group {0} There are no jobs matching the query: job name {0} There are no jobs matching the query: job status {0} Usage:

pacclient.py job
pacclient.py job [-l] [-u user_name | -u all ] [-p hours] job_ID | "job_ID[index_list]"
pacclient.py job -s Pending | Running | Done | Exit | Suspended [-l] [-u user_name | -u all ] [-p hours]
pacclient.py job -n job_name [-l] [-u user_name | -u all ] [-p hours]
pacclient.py job -g jobgroup_name [-l] [-u user_name | -u all ] [-p hours]
pacclient.py -h 

Description:
By default, displays information about jobs submitted by the user running this command.

job_ID | "job_ID[index_list]"
 Displays information about the specified jobs or job arrays.

-l
 Long format. Displays detailed information for each job, job array, or job group in a multiline format.

-u user_name | -u all
 Only displays information about jobs that have been submitted by the specified user. The keyword all specifies all users.

-p hours
 In addition to active jobs, displays information about all Done and Exited jobs that have ended within the specified number of hours.

-s Pending | Running | Done | Exit | Suspended
 Displays information only about jobs that have the specified state.

-n job_name
 Displays information about jobs or job arrays with the specified job name. The wildcard character (*) can be used within a job name, but cannot appear within array indices. For example job* returns jobA and jobarray[1], *AAA*[1] returns the first element in all job arrays with names containing AAA, however job1[*] will not return anything since the wildcard is within the array index.

-g jobgroup_name
 Displays information about jobs attached to the specified job group.

-h
 Displays command usage. The options -s, -n, -g, and job ID cannot be used together. You must specify the job ID. pacclient.py jobaction usage:

pacclient.py jobaction [--help|-h] --action|-a kill|suspend|requeue|resume job_ID

Perform a job action on a job.

For example:
pacclient.py jobaction -a resume 54321

--action|-a kill|suspend|requeue|resume
	Specify the job action. You can kill, suspend, requeue, or resume a job.
job_ID
	Specify the job ID.
[--help|-h]
	Display subcommand usage. pacclient.py jobdata usage:

pacclient.py jobdata [--help|-h] [--list|-l] job_ID


For example:
pacclient.py jobdata -l 1234

job_ID
	Specify the job ID.
[--list|-l]
	List all the files for a job.
[--help|-h]
	Display subcommand usage. Specify the URL of the PAC web services in the format: http://host_name:port_number/[context_path] or https://host_name:port_number/[context_path] You have logged on to PAC as: {0} Specify your password. Specify your user name. URL: pacclient.py logon usage:

pacclient.py logon [--help|-h] [--url|-l URL] [--user|-u user_name] [--pass|-p password]

Logs you in to PAC.

For example:
pacclient.py logon -l http://hostA:8080/ -u user2 -p mypassword

Use double quotes around any value that contains spaces or special characters like *, &, etc.
If any parameter is omitted, you will be prompted interactively.
Once you are logged in, you may run other pacclient commands, until you log out. You will be logged out automatically if you do not run any
pacclient commands for 60 minutes consecutively.

[--url|-l URL]
	Specify the URL of the PAC web service in the format:
	http://host_name:port_number/[context_path] or https://host_name:port_number/[context_path]
[--user|-u user_name]
	Specify your user name.
[--pass|-p password]
	Specify your password.
[--help|-h]
	Display subcommand usage. Username: you have logout successfully. pacclient.py logout usage:

pacclient.py logout [--help|-h]

Logs you out of PAC.

For example:
pacclient.py logout

Once you are logged out, you must log in to run more pacclient commands.
You will be logged out automatically if you do not run any pacclient commands for 60 minutes consecutively.

[--help|-h]
	Display subcommand usage. pacclient.py usage:

ping      --- Check whether the web service is available
logon     --- Log on to IBM Spectrum LSF Application Center
logout    --- Log out from IBM Spectrum LSF Application Center
app       --- List applications or parameters of an application
submit    --- Submit a job
job       --- Show information for one or more jobs
jobaction --- Perform a job action on a job
jobdata   --- List all the files for a job
download  --- Download job data for a job
upload    --- Upload job data for a job
usercmd   --- Perform a user command
pacinfo   --- Displays IBM Spectrum LSF Application Center version, build number and build date
help      --- Display command usage There is not enough memory to upload files. You must log on to PAC. To log on, run pacclient logon. No service was found. There is not enough memory to upload files. pacclient.py pacinfo usage:

pacclient.py pacinfo
pacclient.py pacinfo --help | -h

Displays IBM Spectrum LSF Application Center version, build number and build date Password can not be empty. Permission denied to write the file: %s URL: Specify the URL of the PAC web services in the format: http://host_name:port_number/[context_path] or https://host_name:port_number/[context_path] pacclient.py ping usage:

pacclient.py ping [--help|-h] [--url|-l URL]

Detects whether or not the web service is running at the specified URL.

For example:
pacclient.py ping -l http://hostA:8080/

If -l is omitted, you will be prompted interactively.

[--url|-l URL]
	Specify the URL of the PAC web service in the format:
	http://host_name:port_number/[context_path]
[--help|-h]
	Display subcommand usage. Cannot find the published application: %s. This job cannot be submitted. Start to download... Start to upload... This required argument is missing: -a app_name[:template_name]. To view the command usage, run pacclient.py submit -h.  Cannot open the file: %s The specified file does not exist: %s The input parameters are invalid.To view the command usage, run pacclient.py submit --help. The [Inputfile] section is missing from the file: %s The [Parameter] section is missing from the file: %s The job has been submitted successfully: job ID {0} pacclient.py submit usage:

pacclient.py submit [--help|-h] [--conf|-c file_path ] [--param|-p field_ID=value;[field_ID=value;]...] --app|-a app_name[:template_name]

Submits a job to PAC.

For example:
pacclient.py submit -a "FLUENT" -c C:\mydir\fluentconf.txt -p "CONSOLE_SUPPORT=yes;CAS_INPUT_FILE=C:\mydir\fluent\fluent-test.cas.gz,link"

Use double quotes around any value that contains spaces.
Parameters defined in the command line (-p) override all others; parameters defined in a file (-c) override parameters defined in an application form (-a).

--app|-a app_name[:template_name] 
	Required. Specify the application form to use for default job submission parameters.
	Specify the application name and optionally the name of your customized template.
[--conf|-c file_path ]
	Define the job submission parameters from a file.
	Specify the path to a file on the local host that defines job parameters and input files. The file format is a list of field ID and value pairs:
	* field_ID
		Specify the field ID from the application form template. You must be an administrator to access editing mode and view the field IDs.
	* value
		Specify the value for the field input. If the field requires a file for input, you must also choose to upload the file, copy the file to the job directory, or link the file to the job directory.
		Specify the value in the following format. To specify multiple files, separate with a hash (#):

		file_path,upload[#file_path,upload]
		file_path,copy[#file_path,copy]
		file_path,link[#file_path,link]

		Examples:
		Submit the job and copy the specified input file to the job directory
		/home/user1/myfile,copy

		Submit the job and link the specified files to the job directory
		/home/user1/myfile3,link#/home/user1/myfile4,link

		Upload multiple files to the job directory
		C:\demo\fluent\fluent-test.cas.gz,upload#C:\demo\fluent\fluent-test.cas2.gz,upload

	For example:
	[Parameter]
	JOB_NAME=FF_20100329
	VERSION=6.3.26
	CONSOLE_SUPPORT=No
	[Inputfile]
	FLUENT_JOURNAL=C:\demo\fluent\fluent-test.jou,upload
	CAS_INPUT_FILE=C:\demo\fluent\fluent-test.cas.gz,upload
[--param|-p field_ID=value;[field_ID=value;]...]
	Define the job submission parameters in the command line.
	Specify field ID and value pairs as described in the --conf|-c option.
[--help|-h]
	Display subcommand usage. Submit job failed, No such file or directory: %s The specified file does not exist: %s You do not have read permission on the file: %s The job ID must be a positive integer. The directory cannot be relative if it is remote. Specify an absolute path for the directory. Please specify a job ID if the -d option is omitted or specifies a relative local path. Please specify the source files to upload. pacclient.py upload usage:

pacclient upload  [-d dir_name] -f file_name[,file_name..] job_ID
pacclient upload  -d host_name:dir_name -f file_name[,file_name..]
pacclient upload -h


Description:

Uploads data for a job to the job directory on the web server or the remote directory on a specific host.
By default, if a job ID is specified but no directory is specified, files are uploaded to the job directory on the web server.


Options:

-d dir_name
        Copies files to the specified directory on the web server. The directory can be an
        absolute path on the web server or a relative path to the job directory on the web server.

-d host_name:dir_name
        Copies files to the specified job directory on the host. The directory can be
        an absolute path to the remote job directory on the host, or a relative path to
        the remote job directory on the host.

-f file_name[,file_name..]
        Uploads the specified file. Specify the path. Separate multiple files with a comma.

job_ID
        ID of the job for which to upload files.

-h
        Displays command usage.


Examples:

Upload files to the job directory on the web server
pacclient upload -f /dir1/file1,/dir2/file2 54321

Upload file1 into the result subdirectory under job 101's job directory

pacclient.py upload -d result -f file1 101

Upload file1 into /tmp/result on the web server
pacclient.py upload -d /tmp/result -f file1

Upload file1 into absolute path /tmp/result on remote host
pacclient.py upload -d  host1:/tmp/result -f file1 Failed to connect to web service and file upload failed. Uploading file: {0} to current job directory Uploading file: {0} to {1} Uploading input file: %s pacclient.py usercmd usage:

pacclient.py usercmd -c user_command
pacclient.py -h

Description:

Runs the specified command.

By default, the following LSF commands are allowed:
- bbot
- bchkpnt
- bkill
- bpost
- brequeue
- brestart
- bresume
- brun
- bstop
- btop
- bswitch
- bmig

The administrator can configure support for additional commands in the file
$GUI_CONFDIR/webservice.usercmd.


Options:

-c user_command
   Specify the executable command with its full path and options.

-h
   Displays command usage.


Examples:

Kill job 101 by sending a SIGTERM signal
pacclient.py usercmd -c bkill -s SIGTERM 101

Force checkpoint of job 201 every 5 minutes
pacclient.py usercmd -c bchkpnt -f -p 5 201 The profile Inputfile section or inputfile param format is wrong
see the help. Wrong URL format. proper format: http://hostname:port/ Web services aren't ready on URL: %s 