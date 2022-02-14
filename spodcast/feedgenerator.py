RSS_FEED_FILE_NAME = '.index.php'
RSS_FEED_INFO_EXTENSION = 'info'
RSS_FEED_SHOW_INDEX = 'index'

def RSS_FEED_CODE():
    return r'''<?php
SHOW_INDEX = "''' + RSS_FEED_SHOW_INDEX + r'''";
INFO = "''' + RSS_FEED_INFO_EXTENSION + r'''";
header("Content-type: text/xml");
$feed_name = "Spodcast autofeed";
$feed_description = "Spodcast autofeed";
$base_url = strtok('https://' . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI'], '?');
$feed_logo = "$base_url/.image.jpg";
$feed_link = $base_url;
$allowed_extensions = array('mp4','m4a','aac','mp3','ogg');

$sinfo=SHOW_INDEX.".".INFO;
if(file_exists($sinfo)) {
    $json=file_get_contents($sinfo);
    $info=json_decode($json);
    $feed_name=$info->title;
    $feed_description=$info->description;
    $feed_logo=$info->image;
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

def RSS_INDEX_CODE(bin_path, config_name):
    return r'''<?php
const INFO="''' + RSS_FEED_INFO_EXTENSION + r'''";
const SHOW_INFO="''' + RSS_FEED_SHOW_INDEX + r'''.".INFO;
const SPODCAST="''' + bin_path + r'''";
const SPODCAST_CONFIG="''' + config_name + r'''";
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

if (PHP_SAPI == "cli") {
    if (count($argv) < 2) {
        echo "use: php ".__FILE__." <command> [options...]".PHP_EOL;
        echo "     commands: ".implode("|",CLI_COMMANDS).PHP_EOL;
        die();
    }

    $settings=read(dirname(__FILE__)."/".SETTINGS_INFO);
    $feeds=read(dirname(__FILE__)."/".FEEDS_INFO);
    $SPODCAST_CONFIG=dirname(__FILE__)."/".SPODCAST_CONFIG;

    $command=$argv[1];
    if($command == "refresh") {
        foreach ($feeds as $url => ["title"=>$title,"directory"=>$directory,"max"=>$max,"keep"=>$keep]) {
            if ($max > 0) {
                $output = add_feed($url, $max, true);
                echo(implode(PHP_EOL, $output));
            }
            $episodes=get_episodes($directory);
            if(count($episodes) > $keep) {
                $to_delete=array_splice($episodes, $keep);
                foreach ($to_delete as $episode) {
                    system("rm -f ".escapeshellarg($directory."/".$episode['filename'])." 2>&1");
                    system("rm -f ".escapeshellarg($directory."/".$episode['filename']).".".INFO." 2>&1");
                }
            }
        }
    }
    die();
}

$feeds=get_feeds(dirname(__FILE__));
$settings=get_settings();
$ERROR_MESSAGE=null;
$ERROR_DETAILS=null;

function get_feeds($dir) {
    $spodcast_url=(isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on' ? "https" : "http")."://".$_SERVER['HTTP_HOST'].$_SERVER['REQUEST_URI'];
    foreach(glob($dir."/*/".SHOW_INFO) as $show_info) {
        $episodes=get_episodes(dirname($show_info));
        $json=file_get_contents($show_info);
        $info=json_decode($json);
        $feeds[$info->link]['title']=$info->title;
        $feeds[$info->link]['image']=$info->image;
        $feeds[$info->link]['episodes']=count($episodes);
        $feeds[$info->link]['last']=date("Y-m-d",strtotime($episodes[0]['date']));
        $feeds[$info->link]['directory']=dirname($show_info);
        $feeds[$info->link]['max']=$info->max ?? 2;
        $feeds[$info->link]['keep']=$info->keep ?? 5;
        $feeds[$info->link]['feed']=$spodcast_url.basename(dirname($show_info));
    }
    uasort($feeds, fn ($a, $b) => strnatcmp($a['title'], $b['title']));
    store($feeds, FEEDS_INFO);
    return $feeds;
}

function get_episodes($dir) {
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
    $settings=read(SETTINGS_INFO);
    $spodcast_url=(isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on' ? "https" : "http")."://".$_SERVER['HTTP_HOST'].$_SERVER['REQUEST_URI'];
    $settings['spodcast_url']=$settings['spodcast_url'] ?? $spodcast_url;
    $settings['update_start']=$settings['update_start'] ?? 0;
    $settings['update_rate']=$settings['update_rate'] ?? 1;
    $settings['update_enabled']=$settings['update_enabled'] ?? false;
    store($settings, SETTINGS_INFO);
    return $settings;
}

function get(&$var, $default=null) {
    return isset($var) ? $var : $default;
}

function read($file) {
    if(file_exists($file)) {
        $json=file_get_contents($file);
        $info=json_decode($json, true);
    } else {
        $info=[];
    }
    return $info;
}

function store($info, $file) {
    $f = fopen($file,'w');
    fwrite($f, json_encode($info));
    fclose($f);
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
    $tempfile=system("mktemp");
    file_put_contents($tempfile, implode(PHP_EOL,$crontab));
    $command="crontab ".$tempfile;
    exec($command);
    unlink($tempfile);
}

function get_range($start, $rate) {
    for ($i=0; $i < $rate; $i++) {
        $arr[]=(($start%(24/$rate))+($i*(24/$rate)))%24;
    }
    return implode(",", $arr);
}

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
            submit_crontab($crontab);
        } else {
            if ($index !== NOT_FOUND) {
                array_splice($crontab, $index, 1);
                $crontab[count($crontab)-1]=rtrim($crontab[count($crontab)-1]).PHP_EOL;
                submit_crontab($crontab);
            }
        }
    }
}

function login($username, $password, $return_output=false) {
    $output = null;
    $retval = null;
    $tempfile=system("mktemp");
    $SPODCAST_CONFIG=dirname(__FILE__)."/".SPODCAST_CONFIG;
    file_put_contents($tempfile, "$username $password");
    $command=SPODCAST." -c ".$SPODCAST_CONFIG." --log-level ".LOG_LEVEL." -l ".$tempfile." 2>&1";
    exec($command, $output, $retval);
    unlink($tempfile);
    if ($retval > 0 || $return_output) {
        return $output;
    }
    return SUCCESS;
}

function add_feed($url, $max, $return_output=false) {
    $output = null;
    $retval = null;
    $SPODCAST_CONFIG=dirname(__FILE__)."/".SPODCAST_CONFIG;
    $command=SPODCAST." -c ".$SPODCAST_CONFIG." --max-episodes ".$max." ".escapeshellarg($url)." 2>&1";
    exec($command, $output, $retval);
    if ($retval > 0 || $return_output) {
        return $output;
    }
    return SUCCESS;
}

function delete_feed($url, $return_output=false) {
    $output = null;
    $retval = null;
    $feeds=read(FEEDS_INFO);
    $feed_dir=$feeds[$url]['directory'];
    $command="rm -rf ".$feed_dir." 2>&1";
    exec($command, $output, $retval);
    if ($retval > 0 || $return_output) {
        return $output;
    }
    return SUCCESS;
}

function update_show($url, $field, $value) {
    if (array_search($field, UPDATEABLE) === false) {
        return ["$field is not an updateable field"];
    } else {
        $feeds=read(FEEDS_INFO);
        $show_dir=$feeds[$url]['directory'];
        $show=read($show_dir."/".SHOW_INFO);
        $show[$field]=(int) $value;
        store($show, $show_dir."/".SHOW_INFO);
        return SUCCESS;
    }
}

function show_error($message, $details) {
    header("Location: ./?action=error&message=".urlencode($message)."&details=".urlencode(implode(PHP_EOL,$details)));
    die();
}

switch(get($_GET['action'])) {
case 'refresh':
case 'new':
    $url = get($_GET['url']);
    $result = add_feed($url, MAX_EPISODES);
    if ($result !== SUCCESS) {
        show_error("Add/refresh feed failed", $result);
    }
    header("Location: .");
    die();
case 'delete':
    $url = get($_GET['url']);
    $result = delete_feed($url);
    if ($result !== SUCCESS) {
        show_error("Delete feed failed", $result);
    }
    header("Location: .");
    die();
case 'update':
    $url = get($_GET['url']);
    $field = get($_GET['field']);
    $value = get($_GET['value']);
    $result=update_show($url, $field, $value);
    if ($result !== SUCCESS) {
        show_error("Update failed", $result);
    }
    header("Location: .");
    die();
case 'login':
    $username = get($_GET['username']);
    $password = get($_GET['password']);
    $result = login($username, $password);
    if ($result !== SUCCESS) {
        show_error("Login failed",$result);
    }
    header("Location: .");
    die();
case 'schedule':
    $enable = (get($_GET['enable']) == "true" ? true : false);
    $start = (int) get($_GET['start']);
    $rate = (int) get($_GET['rate']);
    $settings['update_enabled'] = $enable;
    $settings['update_start'] = $start;
    $settings['update_rate'] = $rate;
    store($settings, SETTINGS_INFO);
    update_scheduler($enable, $start, $rate);
    header("Location: .");
    die();
case 'error':
    $ERROR_MESSAGE = get($_GET['message']);
    $ERROR_DETAILS = get($_GET['details']);
default:
    break;
}

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
        .episode, .setgroup, .error { display: flex; flex-wrap: wrap; margin: 0 0 2em 0; padding: 0; font-family: sans-serif; border: 1px solid #F0F0F0; background: #F0F0F0; border-radius: 6px; }
        .setgroup { border: 1px solid black; margin: 1em; }
        .error { border: 2px solid red; margin: 1em; }
        .entry, .setitem, .errorline { display: flex; box-sizing: border-box; flex-grow: 1; width: 100%; padding: 0.4em 0.6em; overflow: hidden; align-items: center; text-align: left; background: #F0F0F0; }
        .comment { font-size: 80%; font-style: italic; }
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

        legend { margin-left: 1.5em; font-size: 120%; border: 1px solid black; border-radius: 6px; background: white; }
        .error legend { border: 2px solid red; }
 
        @media all and (max-width: 500px) {
            .episode { display: block; }
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
        <div class="episode">
            <div class="entry title"><?=$title?></div>
            <div class="entry logo"><img src="<?=$image?>"/></div>
            <div class="entry link"><a target="_blank" href="<?=$url?>"><?=htmlspecialchars($url)?></a></div>
            <div class="entry stats"><?=$last?>&nbsp;(<?=$episodes?>)</div>
            <div class="entry feed"><a target="_blank" href="<?=$feed?>"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-rss" viewBox="0 0 16 16"><path d="M14 1a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h12zM2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2z"/><path d="M5.5 12a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0zm-3-8.5a1 1 0 0 1 1-1c5.523 0 10 4.477 10 10a1 1 0 1 1-2 0 8 8 0 0 0-8-8 1 1 0 0 1-1-1zm0 4a1 1 0 0 1 1-1 6 6 0 0 1 6 6 1 1 0 1 1-2 0 4 4 0 0 0-4-4 1 1 0 0 1-1-1z"/></svg>&nbsp;&nbsp;<?=$feed?></a></div>
            <div class="entry last actions"><div></div><div>sync&nbsp;<select id="max-<?=htmlspecialchars($url)?>" onchange="showUpdate(this,'<?=$url?>','max')"><?php foreach([0,1,2,3,4,5] as $i) { printf("<option value='%d'>%d</option>",$i, $i);}?></select></div><div>keep&nbsp;<select id="keep-<?=htmlspecialchars($url)?>" onchange="showUpdate(this,'<?=$url?>','keep')"><?php foreach([1,2,5,10,25,50,100,250,1000,2500] as $i) { printf("<option value='%d'>%d</option>",$i, $i);}?></select>&nbsp;</div><div><a id="delete" onclick="return confirmDelete('<?=$title?>','<?=$url?>')" href="?action=delete&url=<?=$url?>">delete</a></div><div><a onclick="document.getElementById('loading').classList.remove('hidden'); return true;" href="?action=refresh&url=<?=$url?>">refresh</a></div></div>
        </div>
    <?php endforeach; ?>
    </div>
    <div id="loading" class="hidden">
        <div>
            <h1>Please wait...</h1>
            <p>This may take a while.
            <p>Refresh the page if this takes too long
        </div>
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
            <div class="setitem"><button id="update-enable" name="update-enable">Enable scheduled updates</button></div>
            <div id="update-settings">
            <div class="setitem">Update feed&nbsp;<select id="update-rate"><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="6">6</option><option value="8">8</option><option value="12">12</option><option value="24">24</option></select>&nbsp;times per day starting around&nbsp;<select id="update-start"><?php for ($i=0; $i<=24; $i++) { printf("<option value='%d'>%02d:00</option>",$i, $i);}?></select></div>
            <div class="setitem comment">Updates start 5 to 25 minutes after the hour</div>
            <div class="setitem"><button id="do-update" name="do-update">Update</button>
            <button id="update-disable" name="update-disable">Disable updates</button></div>
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
    <script>
    function newfeed() {
        document.getElementById("loading").classList.remove("hidden");
        window.location.href = '?action=new&url=' + encodeURI(document.getElementById('url').value);
    }
    function login() {
        window.location.href = '?action=login&username=' + document.getElementById('username').value + '&password=' + document.getElementById('password').value;
    }
    function schedule(enable) {
        window.location.href = '?action=schedule&enable=' + enable + '&rate=' + document.getElementById('update-rate').value + '&start=' + document.getElementById('update-start').value;
    }
    function selectElement(id, val) {
        document.getElementById(id).value=val;
    }
    function showUpdate(e,url,field) {
        window.location.href = '?action=update&url=' + encodeURI(url) + '&field=' + field + '&value=' + e.value;
    }
    function confirmDelete(title, url) {
        return confirm('You are about to delete the following feed:\n\nTitle: ' + title + '\nURL: ' + url + '\n\nAre you sure you want to delete this feed?');
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
    schedule_entries.style.display = '<?php echo ($UPDATE_ENABLED ? 'initial' : 'none');?>';
    schedule_enable.style.display = '<?php echo ($UPDATE_ENABLED ? 'none' : 'initial');?>';

    schedule_enable.onclick = function() {
        schedule_entries.style.display = 'initial';
        schedule_enable.style.display = 'none';
    };
    schedule_disable.onclick = function() {
        schedule_entries.style.display = 'none';
        schedule_enable.style.display = 'initial';
        schedule(false);
    };

    selectElement('update-rate', '<?=$UPDATE_RATE?>');
    selectElement('update-start', '<?=$UPDATE_START?>');
    <?php foreach($feeds as $url => ["keep"=>$keep,"max"=>$max]) {
        printf("    selectElement('keep-%s', '%d');\n", htmlspecialchars($url), $keep);
        printf("    selectElement('max-%s', '%d');\n", htmlspecialchars($url), $max);
    }?>
    <?php if ($ERROR_MESSAGE != null) {
        echo "    document.getElementById('error').classList.remove('hidden');";
    }?>
    </script>
</body>
</html>'''
