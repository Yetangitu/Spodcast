RSS_FEED_FILE_NAME = '.index.php'
RSS_FEED_INFO_EXTENSION = 'info'
RSS_FEED_SHOW_INDEX = 'index'
RSS_FEED_CODE = r'''<?php
header("Content-type: text/xml");
$feed_name = "Spodcast autofeed";
$feed_description = "Spodcast autofeed";
$base_url = strtok('https://' . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI'], '?');
$feed_logo = "$base_url/.image.jpg";
$feed_link = $base_url;
$allowed_extensions = array('mp4','m4a','aac','mp3','ogg');

$sinfo="''' + RSS_FEED_SHOW_INDEX + "." + RSS_FEED_INFO_EXTENSION + r'''";
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
            $finfo=$raw_file.".''' + RSS_FEED_INFO_EXTENSION + r'''";
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
