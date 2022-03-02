import re

RSS_FEED_FILE_NAME = '.index.php'
RSS_FEED_INFO_EXTENSION = 'info'
RSS_FEED_SHOW_INDEX = 'index'
RSS_FEED_SHOW_IMAGE = 'image.jpg'
RSS_FEED_VERSION = '$SPODCAST_VERSION$ '
VERSION_NOT_FOUND = 0

def get_index_version(filename) -> str:
    with open(filename, 'rb') as f:
        for line in f.readlines():
            m = re.search(RSS_FEED_VERSION + ' (\d+.\d+.\d+)', str(line))
            if m:
                return int(m[1].replace('.',''))

    return VERSION_NOT_FOUND


def RSS_FEED_CODE(version):
    return r'''<?php
/* ''' + RSS_FEED_VERSION + version + r''' */
const SHOW_INDEX = "''' + RSS_FEED_SHOW_INDEX + r'''";
const INFO = "''' + RSS_FEED_INFO_EXTENSION + r'''";
$PROTOCOL = (empty($_SERVER['HTTPS'])) ? "http://" : "https://";
header("Content-type: text/xml");
$feed_name = "Spodcast autofeed";
$feed_description = "Spodcast autofeed";
$base_url = strtok($PROTOCOL . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI'], '?');
$feed_logo = "$base_url/''' + RSS_FEED_SHOW_IMAGE + r'''";
$feed_link = $base_url;
$allowed_extensions = array('mp4','m4a','aac','mp3','ogg');

$sinfo=SHOW_INDEX.".".INFO;
if(file_exists($sinfo)) {
    $json=file_get_contents($sinfo);
    $info=json_decode($json);
    $feed_name=$info->title;
    $feed_description=$info->description;
    $feed_link=$info->link;
}

?>
<?php echo '<?xml version="1.0" encoding="utf-8"?>';  // use php to output the "<?" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" >
    <channel>
        <title><?php echo $feed_name; ?></title>
        <link><?php echo $feed_link; ?></link>
        <image>
            <url><?php echo $feed_logo; ?></url>
            <title><?php echo $feed_name; ?></title>
            <link><?php echo $feed_link; ?></link>
        </image>
        <description><?php echo $feed_description; ?></description>
        <atom:link href="<?php echo $base_url; ?>" rel="self" type="application/rss+xml" />
<?php
$raw_files = scandir ('.');
usort($raw_files, function($a, $b) {
    return filemtime($a) < filemtime($b);
});

foreach ($raw_files as &$raw_file) {
    $raw_file_info = pathinfo($raw_file);
    $extension = strtolower($raw_file_info['extension']);
    if(!empty($extension)) {
        if(in_array ($extension,$allowed_extensions)) {
            $finfo=$raw_file.".".INFO;
            if(file_exists($finfo)) {
                $json=file_get_contents($finfo);
                $info=json_decode($json);
                echo "        <item>\n";
                echo "            <title>".$info->title."</title>\n";
                echo "            <description>".$info->description."</description>\n";
                echo "            <guid>".$info->guid."</guid>\n";
                echo "            <link>".$base_url.$info->filename."</link>\n";
                echo "            <enclosure url=\"".$base_url.$info->filename."\" length=\"".$info->size."\" type=\"".$info->mimetype."\" />\n";
                echo "            <media:content url=\"".$base_url.$info->filename."\" medium=\"".$info->medium."\" duration=\"".$info->duration."\" type=\"".$info->mimetype."\" />\n";
                echo "            <pubDate>".$info->date."</pubDate>\n";
                echo "            <itunes:duration>".$info->duration."</itunes:duration>\n";
                echo "        </item>\n";
            }
        }
    }
}
?>
    </channel>
</rss>'''

def RSS_INDEX_CODE(bin_path, config_name, version):
    return r'''<?php
/* ''' + RSS_FEED_VERSION + version + r''' */
const INFO="''' + RSS_FEED_INFO_EXTENSION + r'''";
const SHOW_INFO="''' + RSS_FEED_SHOW_INDEX + r'''.".INFO;
const SPODCAST="''' + bin_path + r'''";
const SPODCAST_CONFIG="''' + config_name + r'''";
const SHOW_IMAGE="''' + RSS_FEED_SHOW_IMAGE + r'''";
const FEEDS_INFO="feeds.".INFO;
const SETTINGS_INFO="settings.".INFO;
const MAX_EPISODES=3;
const KEEP_EPISODES=5;
const UPDATEABLE=['max','keep'];
const CLI_COMMANDS=['refresh'];
const SUCCESS='success';
const ERROR='error';
const LOG_LEVEL='warning';
const NOT_FOUND=-1;

$SPODCAST_CONFIG=dirname(__FILE__)."/".SPODCAST_CONFIG;
$SPODCAST_COMMAND=SPODCAST." -c ".$SPODCAST_CONFIG;

# CLI
if (PHP_SAPI == "cli") {
    global $SPODCAST_CONFIG;
    if (count($argv) < 2) {
        echo "use: php ".__FILE__." <command> [options...]".PHP_EOL;
        echo "     commands: ".implode("|",CLI_COMMANDS).PHP_EOL;
        die();
    }

    $settings=read(dirname(__FILE__)."/".SETTINGS_INFO);
    $feeds=read(dirname(__FILE__)."/".FEEDS_INFO);

    $command=$argv[1];
    if($command == "refresh") {
        list($retval, $result) = refresh_shows($feeds);
        if ($retval > 0) {
            echo "An error occurred during refresh, return value was $retval" . PHP_EOL;
        }
        echo implode(PHP_EOL, $result);
    }
    die();
}

# CGI/API
$PROTOCOL = (empty($_SERVER['HTTPS'])) ? "http://" : "https://";
$SPODCAST_URL = $PROTOCOL . $_SERVER['HTTP_HOST'] . parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$feeds=get_feeds(dirname(__FILE__));
$settings=get_settings();
$config=get_spodcast_config();
$ERROR_MESSAGE=null;
$ERROR_DETAILS=null;

function get_feeds($dir) {
    global $SPODCAST_URL;
    foreach(glob($dir."/*/".SHOW_INFO) as $show_info) {
        $episodes=get_episodes(dirname($show_info));
        $json=file_get_contents($show_info);
        $info=json_decode($json);
        $feeds[$info->link]['title']=$info->title;
        $feeds[$info->link]['image']=$info->image;
        $feeds[$info->link]['episodes']=count($episodes);
        $feeds[$info->link]['last']=date("Y-m-d",strtotime($episodes[0]['date']));
        $feeds[$info->link]['directory']=dirname($show_info);
        $feeds[$info->link]['max']=$info->max ?? MAX_EPISODES;
        $feeds[$info->link]['keep']=$info->keep ?? KEEP_EPISODES;
        $feeds[$info->link]['feed']=$SPODCAST_URL.basename(dirname($show_info));
    }
    uasort($feeds, fn ($a, $b) => strnatcmp($a['title'], $b['title']));
    store($feeds, FEEDS_INFO);
    return $feeds;
}

function get_episodes($dir) {
    $episodes=[];
    foreach(glob($dir."/*.".INFO) as $episode_info) {
        if(basename($episode_info) == SHOW_INFO) {
            continue;
        }
        $json=file_get_contents($episode_info);
        $info=json_decode($json);
        $episodes[]=["filename"=>$info->filename,"date"=>$info->date,"title"=>$info->title];
    }
    usort($episodes, fn ($a, $b) => strtotime($b["date"]) - strtotime($a["date"]));
    return $episodes;
}

function get_settings() {
    global $SPODCAST_URL;
    $settings=read(SETTINGS_INFO);
    $settings['spodcast_url']=$settings['spodcast_url'] ?? $SPODCAST_URL;
    $settings['update_start']=$settings['update_start'] ?? 0;
    $settings['update_rate']=$settings['update_rate'] ?? 1;
    $settings['update_enabled']=$settings['update_enabled'] ?? false;
    $settings['log_level']=$settings['log_level'] ?? LOG_LEVEL;
    store($settings, SETTINGS_INFO);
    return $settings;
}

function get_spodcast_config() {
    global $SPODCAST_CONFIG;
    $config=read($SPODCAST_CONFIG);
    return $config;
}

function get(&$var, $default=null) {
    return isset($var) ? $var : $default;
}

function read($file) {
    if(is_readable($file)) {
        $json=file_get_contents($file);
        $info=json_decode($json, true);
    } else {
        $info=[];
    }
    return $info;
}

function store($info, $file) {
    $f = fopen($file,'w');
    $result = fwrite($f, json_encode($info));
    fclose($f);
    return ($result === false) ? ERROR : SUCCESS;
}

function cron_signature($crontab, $CRON_SIGNATURE) {
    $index = 0;
    foreach ($crontab as $line) {
        if (strpos($line, $CRON_SIGNATURE)  !== false) {
            return $index;
        }
        $index++;
    }
    return NOT_FOUND;
}

function debug($var) {
    ob_start();
    var_dump($var);
    error_log(ob_get_clean());
}

function submit_crontab($crontab) {
    $retval = null;
    $output = null;
    $tempfile=tempnam(sys_get_temp_dir(), 'spodcast');
    file_put_contents($tempfile, implode(PHP_EOL,$crontab));
    $command="crontab ".$tempfile;
    exec($command, $output, $retval);
    unlink($tempfile);

    return [$retval, $output];
}

function get_range($start, $rate) {
    for ($i=0; $i < $rate; $i++) {
        $arr[]=(($start%(24/$rate))+($i*(24/$rate)))%24;
    }
    return implode(",", $arr);
}

function background_check_id($id) {
    $runfile = md5($id).".json";
    $log = md5($id).".log";
    if (is_readable($runfile)) {
        $info = read($runfile);
        if (background_check($info['pid'])) {
            return true;
        }
        unlink($runfile);
        unlink($log);
    }
    return false;
}

function background_check($pid) {
    try {
        $result = shell_exec(sprintf("ps %d", $pid));
        if (count(preg_split("/\n/", $result)) > 2) {
            return true;
        }
    } catch(Exception $e) {}
    return false;
}

# [ status, output ] return functions
function update_scheduler($enable, $start, $rate) {
    $CRON_SIGNATURE="SPODCAST:".dirname(__FILE__);
    $crontab=null;
    $retval=null;
    exec("crontab -l", $crontab, $retval);
    if ($retval == 0) {
        $index=cron_signature($crontab, $CRON_SIGNATURE);
        if ($enable == true) {
            if($index !== NOT_FOUND) {
                array_splice($crontab, $index, 1);
            }
            $crontab[]=sprintf("%d %s * * * php %s refresh # %s".PHP_EOL, rand(5,25), get_range($start, $rate),  __FILE__, $CRON_SIGNATURE);
            return submit_crontab($crontab);
        } else {
            if ($index !== NOT_FOUND) {
                array_splice($crontab, $index, 1);
                $crontab[count($crontab)-1]=rtrim($crontab[count($crontab)-1]).PHP_EOL;
                return submit_crontab($crontab);
            }
        }
    } else {
        return [$retval, "failed to update scheduler"];
    }
}

function login($username, $password, $return_output=false) {
    global $SPODCAST_COMMAND;
    global $settings;
    $output = null;
    $retval = null;
    $tempfile=tempnam(sys_get_temp_dir(), 'spodcast');
    file_put_contents($tempfile, "$username $password");
    $command=$SPODCAST_COMMAND . " --log-level " . $settings['log_level'] . " -l ".$tempfile." 2>&1";
    exec($command, $output, $retval);
    unlink($tempfile);

    return [$retval, $output];
}

function background_run($command, $id) {
    $retval=null;
    $md5 = md5($id);
    $runfile = $md5.".json";
    $output = $md5.".log";
    $cmd = sprintf("nohup %s > %s 2>&1 & echo $!", $command, $output);
    exec($cmd, $pid, $retval);
    if ($retval == 0 && count($pid) > 0 && $pid[0] > 0) {
        $info['command']=$command;
        $info['log']=$output;
        $info['pid']=(int) $pid[0];
        store($info, $runfile);
        return [$retval, $pid[0]];
    } else {
        return [$retval, 0];
    }
}

function background_add_feed($url, $max) {
    global $SPODCAST_COMMAND;
    global $settings;
    $output = null;
    $retval = null;
    $command=$SPODCAST_COMMAND  . " --log-level " . $settings['log_level'] . " --max-episodes ".(int)$max." ".escapeshellarg($url);
    list($retval, $pid) = background_run($command, $url);
    if ($retval == 0 && (int) $pid > 0) {
        return [$retval, $pid];
    }
    return [$retval, 0];
}


function add_feed($url, $max) {
    global $SPODCAST_COMMAND;
    global $settings;
    $output = null;
    $retval = null;
    $command=$SPODCAST_COMMAND  . " --log-level " . $settings['log_level'] . " --max-episodes ".(int)$max." ".escapeshellarg($url)." 2>&1";
    exec($command, $output, $retval);
    return [$retval, $output];
}

function update_feed($url, $max, $keep, $feeds) {
    $output = null;
    $retval = null;
    if ($max > 0) {
    list($retval,$output) = add_feed($url, $max);
        if ($retval > 0) {
            return [$retval, $output];
        }
    }
    $directory=$feeds[$url]['directory'];
    $episodes=get_episodes($directory);
    if(count($episodes) > $keep) {
        $to_delete=array_splice($episodes, $keep);
        foreach ($to_delete as $episode) {
            $command="rm -f ".escapeshellarg($directory."/".$episode['filename'])." 2>&1";
            exec($command, $output, $retval);
            if ($retval > 0) {
                return [$retval, $output];
            }
            $command="rm -f ".escapeshellarg($directory."/".$episode['filename']).".".INFO." 2>&1";
            exec($command, $output, $retval);
            if ($retval > 0) {
                return [$retval, $output];
            }
        }
    }
    return [$retval, $output];
}

function delete_feed($url, $return_output=false) {
    $output = null;
    $retval = null;
    $feeds=read(FEEDS_INFO);
    $feed_dir=$feeds[$url]['directory'];
    $command="rm -rf ".$feed_dir." 2>&1";
    exec($command, $output, $retval);
    return [$retval, $output];
}

function update_show($url, $field, $value) {
    if (array_search($field, UPDATEABLE) === false) {
        return [1, "$field is not an updateable field"];
    } else {
        $feeds=read(FEEDS_INFO);
        $show_dir=$feeds[$url]['directory'];
        $show=read($show_dir."/".SHOW_INFO);
        $show[$field]=$value;
        store($show, $show_dir."/".SHOW_INFO);
        return [0, "$field set to $value"];
    }
}

function refresh_shows($feeds) {
    $result = [];
    $status = 0;
    foreach ($feeds as $url => ["title"=>$title, "directory"=>$directory, "max"=>$max, "keep"=>$keep]) {
        $output = null;
        $retval = 0;
        list($retval, $output) = update_feed($url, $max, $keep, $feeds, true);
        if ($retval > 0) {
            $status = $retval;
        }
        $result = array_merge($result, $output);
    }
    return [$status, $result];
}

# terminating functions

function show_error($message, $details) {
    header("Location: ./?action=error&message=".urlencode($message)."&details=".urlencode(implode(PHP_EOL,$details)));
    die();
}

function json_response($info) {
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($info, true);
    exit();
}

# CGI commands

switch(get($_GET['action'])) {

case 'refresh':
    $url = get($_POST['url']);
    $max = (int) get($_POST['max']) ?? MAX_EPISODES;
    $keep = (int) get($_POST['keep']) ?? KEEP_EPISODES;
    $info['url']=$url;
    $info['show']=$feeds[$url];
    $info['id']=basename($url);
    if ($max > $keep) {
        $info['result'] = "It does not make sense for the number of episodes to refresh to be larger than the number of episodes to keep.";
        $info['status'] = 'ERROR';
    } else {
        list($result,$output) = update_feed($url, $max, $keep, $feeds, false);
        $info['status'] = ($result == 0) ? 'SUCCESS': 'ERROR';
        if ($result != 0) {
            $info['result'] = "Refresh failed";
        }
    }
    json_response($info);

case 'new':
    $url = get($_POST['url']);
    list($result, $output) = background_add_feed($url, MAX_EPISODES, false);
    $info['url']=$url;
    $info['show']=$feeds[$url] ?? null;
    $info['id']=basename($url);
    $info['status']= ($result == 0) ? 'SUCCESS': 'ERROR';
    json_response($info);

case 'update':
    $url = get($_POST['url']);
    $field = get($_POST['field']);
    $value = get($_POST['value']);
    if (in_array(strtolower($field), UPDATEABLE)) {
        list($result, $output) = update_show($url, $field, $value);
        if ($result == 0) {
            $info['result'] = $output;
            $info['status'] = 'SUCCESS';
        } else {
            $info['result'] = "Update failed";
            $info['status'] = 'ERROR';
        }
    } else {
        $info['result'] = "$field can not be updated";
        $info['status'] = 'ERROR';
    }

    json_response($info);

case 'schedule':
    $enable = (get($_POST['enable']) == "true" ? true : false);
    $start = (int) get($_POST['start']);
    $rate = (int) get($_POST['rate']);
    $settings['update_enabled'] = $enable;
    $settings['update_start'] = $start;
    $settings['update_rate'] = $rate;
    $result = store($settings, SETTINGS_INFO);
    if ($result === ERROR) {
        $info['status'] = 'ERROR';
        $info['result'] = 'Could not store scheduler preferences, giving up';
    } else {
        list($result, $output) = update_scheduler($enable, $start, $rate);
        if ($result == 0) {
            $info['status'] = 'SUCCESS';
            $info['result'] = ($enable === true) ? "Scheduled updates enabled, $rate times per day starting at $start:00" : 'Scheduled updates disabled';
        } else {
            $info['status'] = 'ERROR';
            $info['result'] = implode(PHP_EOL, $result);
        }
    }
    json_response($info);

case 'transcode':
    $enable = (get($_POST['enable']) == "true" ? true : false);
    $config['TRANSCODE']=$enable;
    $result = store($config, $SPODCAST_CONFIG);
    if ($result === SUCCESS) {
        $info['status'] = 'SUCCESS';
        $info['result'] = ($enable) ? 'Transcoding enabled' : 'Transcoding disabled';
    } else {
        $info['status'] = 'ERROR';
        $info['result'] = 'Could not enable transcoding: can not write to config file';
    }
    json_response($info);

case 'logging':
    $level = get($_POST['level']) ?? LOG_LEVEL;
    $config['LOG_LEVEL']=$level;
    if (in_array(strtolower($level), ['critical','error','warning','info','debug'])) {
        $result = store($config, $SPODCAST_CONFIG);
        if ($result === SUCCESS) {
            $info['status'] = 'SUCCESS';
            $info['result'] = 'Log level set to '. $level;
        } else {
            $info['status'] = 'ERROR';
            $info['result'] = 'Could not change log level: can not write to Spodcast config file';
        }
    } else {
        $info['status'] = 'ERROR';
        $info['result'] = 'Invalid log level ' . $level;
    }
    json_response($info);

case 'status':
    $url = get($_POST['url']);
    $info['url'] = $url;
    $info['show']=$feeds[$url] ?? null;
    $info['id'] = basename($url);
    $info['status'] = background_check_id($url) ? 'ACTIVE' : 'READY';
    json_response($info);

case 'delete':
    $url = get($_POST['url']);
    $info['url'] = $url;
    $info['id'] = basename($url);
    list($result, $output) = delete_feed($url);
    if ($result !== 0) {
        $info['status'] = 'ERROR';
        $info['result'] = "Delete feed failed: " . implode(PHP_EOL, $output);
    } else {
        $info['status'] = 'SUCCESS';
        $info['result'] = "Deleted <i>" . $feeds[$url]['title'] . "</i>" ;
    }
    json_response($info);

case 'login':
    $username = get($_POST['username']);
    $password = get($_POST['password']);
    list($result, $output) = login($username, $password);
    if ($result === 0) {
        $info['status'] = 'SUCCESS';
        $info['result'] = 'Login succeeded';
    } else {
        $info['status'] = 'ERROR';
        $info['result'] = 'Login failed for user '. $username;
    }
    json_response($info);

case 'update_shows':
    list($result, $output) = refresh_shows($feeds);
    $info['status'] = ($result == 0) ? 'SUCCESS' : 'ERROR';
    $info['result'] = $output;
    json_response($info);

case 'error':
    $ERROR_MESSAGE = get($_POST['message']);
    $ERROR_DETAILS = get($_POST['details']);
default:
    break;
}

$ACTIVE=[];

foreach (array_keys($feeds) as $url) {
    if (background_check_id($url)) {
        $ACTIVE[$url]=true;
    }
}

$TRANSCODE_ENABLED=(array_key_exists('TRANSCODE', $config)) ? (($config['TRANSCODE'] == "True") ? true : false) : false;
$LOG_LEVEL=$config['LOG_LEVEL'];
$UPDATE_ENABLED=$settings['update_enabled'];
$UPDATE_START=$settings['update_start'];
$UPDATE_RATE=$settings['update_rate'];
?>
<html>
<head>
    <title>Spodcast feed manager</title>
    <style>
        div, body, html { background-color: white; margin: 0.5em; }
        div#new-feed { margin: 0em; display: flex; }
        input#url { flex: 1; }
        div#settings-header { text-align: right; }
        div input, div button { height: 2em; font-size: 1.2em; margin: 0 1em 1em 0; }
        div#loading { position: fixed; display: flex; width: 100%; height: 100%; top: 0; left: 0; opacity: 0.8; background-color: #fff; z-index: 99; justify-content: center; align-items: center; font-size: 200%; }
        div#settings, div#error { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 99; opacity: 0.95; margin: 0.5em auto; }
        div.hidden { visibility: hidden; }
        div.overlay { position: absolute; width: 100%; height: 100%; left: 0; right: 0; background: white; opacity: 0.5; z-index: 100; display: flex; justify-content: center; align-items: center; }
        .show, .setgroup, .error { position: relative; display: flex; flex-wrap: wrap; margin: 0 0 2em 0; padding: 0; font-family: sans-serif; border: 1px solid #F0F0F0; background: #F0F0F0; border-radius: 6px; }
        .show .placeholder { height: 4em; }
        .setgroup { border: 1px solid black; margin: 1em; }
        .error { border: 2px solid red; margin: 1em; }
        .entry, .setitem, .errorline { display: flex; box-sizing: border-box; flex-grow: 1; width: 100%; padding: 0.4em 0.6em; overflow: hidden; align-items: center; text-align: left; background: #F0F0F0; }
        .comment { font-size: 80%; font-style: italic;}
        .entry > a { text-decoration: none; color: black; }
        .entry > a:hover { color: red; }
        .title { background: linear-gradient(90deg, #E0E0E0, #F0F0F0); border-radius: 6px; }
        .link, .title { width: 40%; }
        .title { text-transform: uppercase; }
        .logo { width: 5%; min-width: 5em; flex-grow: 0; background: #F0F0F0; }
        .logo img { width: 4em; height: 4em; }
        .stats { width: 10%; min-width: 10em; }
        .feed { font-size: 90%; }
        .actions { display: flex; flex-direction: row; align-content: flex-end; flex: wrap; width: 100vw; background: #F0F0F0; }
        .actions div:nth-of-type(1) { flex-grow: 1; }
        .actions div { margin: 0 0 0 2em; background: inherit; }
        .actions a { display: block; border: 1px solid #999; padding: 4px; color: black; text-decoration: none; border-radius: 5px; font-weight: bold; color: #222; background: white; }
        .actions a:hover { color: white; background: #222; }
        #delete { color: red; background: white; }
        #delete:hover { color: white; background: red; }
        #update-settings { background: inherit; }

        .loader { display: inline-block; width: 4em; height: 4em; }
        .loader:after { content: " "; display: block; width: 2em; height: 2em; margin: 8px; border-radius: 50%; border: 6px solid black; border-color: black transparent black transparent; animation: loader 1.2s linear infinite; }
        @keyframes loader { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        #toast { position: absolute; width: 33%; left: 33%; bottom: 2em; padding: 2em; border-radius: 6px; background: #F0F0F0; font-size: 1.2em; font-family: sans-serif; z-index: 200; text-align: center;}
        #toast.success { border: 1px solid black; }
        #toast.error { border: 6px solid red; }

        legend { margin-left: 1.5em; font-size: 100%; border: 1px solid black; border-radius: 6px; background: white; padding: 0.1em 0.5em; }
        .error legend { border: 2px solid red; }
 
        @media all and (max-width: 500px) {
            .show { display: block; }
            .entry { width: 95% !important; }
            .last { margin-bottom: 1em; }
            .actions { flex-direction: column; align-items: flex-end; }
            .actions div { margin: 0.2em 0; }
        }
    </style>
</head>
<body>
    <div id="new-feed">
        <input id="url" name="feed" type="text" placeholder="Spotify show/episode url">
        <button id='new'>Add</button>
        <button id='opensettings' onclick="document.getElementById('settings').classList.remove('hidden'); return false;">Settings</button>
    </div>
    <div id="feed-list">
    <?php foreach($feeds as $url => ["title"=>$title,"image"=>$image,"episodes"=>$episodes,"last"=>$last,"max"=>$max,"keep"=>$keep,"feed"=>$feed]): ?>
        <div class="show" id="<?php echo basename($url) ?>">
            <div class="overlay loader <?php echo (array_key_exists($url, $ACTIVE)) ? "" : "hidden" ?>"></div>
            <div class="entry title"><?=$title?></div>
            <div class="entry logo"><img src="<?=$feed."/".SHOW_IMAGE?>"/></div>
            <div class="entry link"><a target="_blank" href="<?=$url?>"><?=htmlspecialchars($url)?></a></div>
            <div class="entry stats" id="stats-<?php echo basename($url) ?>"><?=$last?>&nbsp;(<?=$episodes?>)</div>
            <div class="entry feed"><a target="_blank" href="<?=$feed?>"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-rss" viewBox="0 0 16 16"><path d="M14 1a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h12zM2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2z"/><path d="M5.5 12a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0zm-3-8.5a1 1 0 0 1 1-1c5.523 0 10 4.477 10 10a1 1 0 1 1-2 0 8 8 0 0 0-8-8 1 1 0 0 1-1-1zm0 4a1 1 0 0 1 1-1 6 6 0 0 1 6 6 1 1 0 1 1-2 0 4 4 0 0 0-4-4 1 1 0 0 1-1-1z"/></svg>&nbsp;&nbsp;<?=$feed?></a></div>
            <div class="entry last actions"><div></div><div>sync&nbsp;<select id="max-<?=basename($url)?>" onchange="showUpdate(this,'<?=$url?>','max')"><?php foreach([0,1,2,3,4,5] as $i) { printf("<option value='%d'>%d</option>",$i, $i);}?></select></div><div>keep&nbsp;<select id="keep-<?=basename($url)?>" onchange="showUpdate(this,'<?=$url?>','keep')"><?php foreach([1,2,5,10,25,50,100,250,1000,2500] as $i) { printf("<option value='%d'>%d</option>",$i, $i);}?></select>&nbsp;</div><div><a id="delete" onclick="confirmDelete('<?=$title?>','<?=$url?>')">delete</a></div><div><a id="refresh" onclick="refresh('<?=$url?>')">refresh</a></div></div>
        </div>
    <?php endforeach; ?>
    </div>
    <div id="settings" class="hidden">
        <div id="settings-header">
            <button id='closesettings' onclick="document.getElementById('settings').classList.add('hidden'); return false;">Close</button>
        </div>
        <fieldset id="credentials" class="setgroup">
            <legend>Spotify login</legend>
            <div class="setitem"><input id="username" name="username" type="text" placeholder="Spotify username">&nbsp;
            <input id="password" name="password" type="password" placeholder="Spotify password"></div>
            <div class="setitem"><button id="do-login" name="do-login">Login to Spotify</button></div>
        </fieldset>
        <fieldset id="scheduler" class="setgroup">
            <legend>Feed update schedule</legend>
            <div class="setitem comment"><span>There are two ways to keep your shows up to date:<ol><li>using the native scheduler</li><li>through webcron: <b><?=$SPODCAST_URL.'?action=update_shows'?></b></li></ol>Enable updates through the native scheduler by clicking the button. If this does not work - e.g. because the web server user is not allowed to add cron jobs or because the web server runs in a Docker container which does not support such jobs - you can point any web client (curl or wget work fine here) at the webcron endpoint (see #2) to initiate an update run. Configure a user cron job for curl/wget to access the refresh endpoint at the desired times for a user experience similar to using the native scheduler.</span>  </div>
            <div class="setitem"><button id="update-enable" name="update-enable">Enable scheduled updates</button></div>
            <div id="update-settings">
            <div class="setitem">Update feed&nbsp;<select id="update-rate"><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="6">6</option><option value="8">8</option><option value="12">12</option><option value="24">24</option></select>&nbsp;times per day starting around&nbsp;<select id="update-start"><?php for ($i=0; $i<=24; $i++) { printf("<option value='%d'>%02d:00</option>",$i, $i);}?></select></div>
            <div class="setitem comment">Updates start 5 to 25 minutes after the hour</div>
            <div class="setitem"><button id="do-update" name="do-update">Update schedule</button>
            <button id="update-disable" name="update-disable">Disable updates</button></div>
            </fieldset>
        <fieldset id="transcode" class="setgroup">
            <legend>Transcode</legend>
            <div class="setitem comment"><span>Some devices - mainly Apple iOS - do not support open audio codecs like those used by Spotify. For such devices Spodcast can transcode ogg streams to mp3. This is an expensive operation which can take a substantial amount of time, especially on less powerful hardware. Only enable this option when there are no other options.</span></div>
            <div class="setitem"><button id="transcode-enable" name="transcode-enable">Enable transcoder</button><button id="transcode-disable" name="transcode-disable">Disable transcoder</button></div>
        </fieldset>
        <fieldset id="logging" class="setgroup">
            <legend>Logging</legend>
            <div class="setitem comment"><span>The default log level shows which episodes have been downloaded. Change the log level to get more (or less) elaborate information on what Spodcast is up to. Log messages are reported in plain text format through scheduled updates and json-encoded through the webcron endpoint.</span></div>
            <div class="setitem"><select id="log-level" onchange="logUpdate(this)"><?php foreach([['CRITICAL','Only show critical errors'],['ERROR','Show error messages'],['WARNING','Show which episodes have been downloaded'],['INFO','Show downloaded as well as skipped episodes'],['DEBUG','Show detailed internal information for debugging purposes']] as $s) { printf("<option value='%s'>%s</option>",$s[0], $s[1]);}?></select></div>
        </fieldset>


        </div>
    </div>
    <div id="error" class="hidden">
    <fieldset id="errormessage" class="error">
        <legend>Error: <?=$ERROR_MESSAGE?></legend>
        <div class="errorline"><pre><?=$ERROR_DETAILS?></pre></div>
        <div class="errorline"><button id="hide-error" onclick="window.location.href='.'; return false;">Close this message</button></div>
    </fieldset>
    </div>
    <div class="hidden" id="toast"></div>
    <script>
    function xhr(type, url, data, options) {
        options = options || {};
        var request = new XMLHttpRequest();
        request.open(type, url, true);
        if(type === "POST") {
            request.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
        }
        request.onreadystatechange = function () {
            if (this.readyState === 4) {
                if (this.status >= 200 && this.status < 400) {
                    options.success && options.success(parse(this.responseText));
                } else {
                    options.error && options.error(this.status);
                }
            }
        };
        request.send(data);
    }
    function parse(text) {
        try {
            return JSON.parse(text);
        } catch(e) {
            return text;
        }
    }
    function basename(path) {
        return path.replace(/.*\//, '');
    }
    function newfeed() {
        xhr("POST", '?action=new', 'url=' + encodeURI(document.getElementById('url').value), {success:addShow,error:removeShade});
    }
    function addShow(info) {
        title="Adding show (" + info.url + "), please wait...";
        show=document.createElement('div'); show.setAttribute('class', 'show placeholder'); show.setAttribute('id', info.id);
        shade=document.createElement('div'); shade.setAttribute('class', 'overlay');
        logo=document.createElement('div'); logo.setAttribute('class', 'entry logo loader');
        title=document.createElement('div'); title.setAttribute('class', 'entry title');
        feedlist=document.getElementById('feed-list');
        show.appendChild(shade); show.appendChild(title); show.appendChild(logo);
        title.innterHTML = title;
        first=feedlist.firstElementChild;
        feedlist.insertBefore(show, first);
        waitUpdate(info);
    }
    function login() {
        xhr("POST", '?action=login', 'username=' + document.getElementById('username').value + '&password=' + document.getElementById('password').value, {success:showToast, error:showToast});
    }
    function refresh(url) {
        unhide(basename(url));
        id = basename(url);
        max=document.getElementById('max-' + id).value;
        keep=document.getElementById('keep-' + id).value;
        xhr("POST", '?action=refresh', 'url=' + encodeURI(url) + '&max=' + max + '&keep=' + keep, {success:wait, error:removeShade});
    }
    function waitUpdate(info) {
        if (info.status == 'READY' || info.status == 'ERROR') {
            window.location.href = '';
        }
        if (info.show != null) {
            document.getElementById(info.id).childNodes.item(1).innerHTML = "Adding show: " + info.show.title + " (" + info.show.episodes + " episodes of 3 downloaded)...";
        } else {
            document.getElementById(info.id).childNodes.item(1).innerHTML = "Adding show: " + info.url + "...";
        }
        setTimeout(function() {
                xhr("POST", '?action=status', 'url=' + encodeURI(info.url), {success:waitUpdate, error:removeShade});
                }, 2000);
    }
    function wait(info) {
        if (info.status == 'READY' || info.status == 'ERROR') {
            document.getElementById('stats-' + info.id).innerHTML = info.show.last + '&nbsp;(' + info.show.episodes + ')';
            hide(info.id);
        } else { 
            if (info.show != null) {
                document.getElementById('stats-' + info.id).innerHTML = info.show.last + '&nbsp;(' + info.show.episodes + ')';
            }
            setTimeout(function() {
                    xhr("POST", '?action=status', 'url=' + encodeURI(info.url), {success:wait, error:removeShade});
                    }, 2000);
        }
    }
    function removeShade(info) {
        hide(info.id);
    }
    function hide(id) {
        document.getElementById(id).firstElementChild.classList.add('hidden');
    }
    function unhide(id) {
        document.getElementById(id).firstElementChild.classList.remove('hidden');
    }
    function schedule(enable) {
        xhr("POST", '?action=schedule', 'enable=' + enable + '&rate=' + document.getElementById('update-rate').value + '&start=' + document.getElementById('update-start').value, {success:showToast, error:showToast});
    }
    function transcode(enable) {
        xhr("POST", '?action=transcode', 'enable=' + enable, {success:showToast, error:showToast});
    }
    function logUpdate(e) {
        xhr("POST", '?action=logging', 'level=' + e.value, {success:showToast, error:showToast});
    }
    function selectElement(id, val) {
        document.getElementById(id).value=val;
    }
    function showUpdate(e,url,field) {
        id = basename(url);
        max=document.getElementById('max-' + id);
        keep=document.getElementById('keep-' + id);
        maxval = parseInt(max.value);
        keepval = parseInt(keep.value);
        if(maxval > keepval) {
            keeper = (maxval > 2) ? 5 : 2;
            if (confirm("Sync count " + maxval + " is higher than Keep count " + keepval + "\n\n" +
                "It does not make sense to refresh more expisodes than are kept in cache." +
                "Press OK to continue, Keep will be set to " + keeper + ". Otherwise press Cancel")) {
                keep.value = keeper;
            } else {
                keep.value = keepval;
                max.value = maxval;
                return false;
            }
        }
        xhr("POST", '?action=update', 'url=' + encodeURI(url) + '&field=' + field + '&value=' + e.value, {success:showToast, error:showToast});
    }
    function confirmDelete(title, url) {
        if (confirm('You are about to delete the following feed:\n\nTitle: ' + title + '\nURL: ' + url + '\n\nAre you sure you want to delete this feed?')) {
            xhr("POST", '?action=delete', 'url=' + encodeURI(url), {success:deleteShow, error:showToast});
        }
        return false;
    }
    function deleteShow(info) {
        document.getElementById(info.id).remove();
        showToast(info);
    }
    function showToast(info) {
        var toast=document.getElementById('toast');
        if (info.status == 'ERROR') {
            toast.classList.remove('success');
            toast.classList.add('error');
        } else {
            toast.classList.remove('error');
            toast.classList.add('success');
        }
        toast.innerHTML=info.result;
        toast.classList.remove("hidden");
        window.setTimeout(function() {
            toast = document.getElementById('toast');
            toast.classList.add("hidden");
            toast.classList.replace('error', 'success');
            toast.innerHTML="";
        }, 2000);
    }

    document.getElementById('new').onclick = function() {
        newfeed();
    };
    document.getElementById('do-login').onclick = function() {
        login();
    };
    document.getElementById('do-update').onclick = function() {
        schedule(true);
    };
    document.getElementById('url').onkeydown = function(e) {
        if(e.keyCode == 13) {
            newfeed();
        }
    };

    var schedule_enable = document.getElementById('update-enable');
    var schedule_disable = document.getElementById('update-disable');
    var schedule_entries = document.getElementById('update-settings');
    var transcode_enable = document.getElementById('transcode-enable');
    var transcode_disable = document.getElementById('transcode-disable');
    schedule_entries.style.display = '<?php echo ($UPDATE_ENABLED ? 'initial' : 'none');?>';
    schedule_enable.style.display = '<?php echo ($UPDATE_ENABLED ? 'none' : 'initial');?>';
    transcode_enable.style.display = '<?php echo ($TRANSCODE_ENABLED ? 'none' : 'initial');?>';
    transcode_disable.style.display = '<?php echo ($TRANSCODE_ENABLED ? 'initial' : 'none');?>';

    schedule_enable.onclick = function() {
        schedule_entries.style.display = 'initial';
        schedule_enable.style.display = 'none';
        schedule(true);
    };
    schedule_disable.onclick = function() {
        schedule_entries.style.display = 'none';
        schedule_enable.style.display = 'initial';
        schedule(false);
    };
    transcode_enable.onclick = function() {
        transcode_enable.style.display = 'none';
        transcode_disable.style.display = 'initial';
        transcode(true);
    };
    transcode_disable.onclick = function() {
        transcode_enable.style.display = 'initial';
        transcode_disable.style.display = 'none';
        transcode(false);
    };
    selectElement('update-rate', '<?=$UPDATE_RATE?>');
    selectElement('update-start', '<?=$UPDATE_START?>');
    selectElement('log-level', '<?=$LOG_LEVEL?>');
    <?php foreach($feeds as $url => ["keep"=>$keep,"max"=>$max]) {
        printf("    selectElement('keep-%s', '%d');\n", basename($url), $keep);
        printf("    selectElement('max-%s', '%d');\n", basename($url), $max);
    }?>
    <?php if ($ERROR_MESSAGE != null) {
        echo "    document.getElementById('error').classList.remove('hidden');";
    }?>
    </script>
</body>
</html>'''

