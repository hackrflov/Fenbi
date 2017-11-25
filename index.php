<!DOCTYPE html>
<html>
<head lang="zh">
    <title>粉笔公考题库</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <!-- CSS Files -->
    <link href="https://cdn.bootcss.com/bootstrap/3.3.7/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <?php 
        function to_array($str) {
            $str = str_replace('u\'', '"', $str);
            $str = str_replace('\'', '"', $str);
            $str = str_replace('[p]', '<p>', $str);
            $str = str_replace('[/p]', '</p>', $str);
            return json_decode($str, true);
        }
        $filename = 'tmp.txt';
        $handle = fopen($filename, "r");
        $contents = fread($handle, filesize($filename));
        fclose($handle);
        //$data = json_decode($contents);
        $params = to_array($contents);
        $alpha = range('A', 'Z');
    ?>
    <div class="container">
    <?php 
        $material = $params['material']; 
        if ($material) {
            echo '材料<br><br>'.$material['content'];
        }
    ?>
    </div>
    <br><br>
    <div class="container">
    <?php echo $params['content']; ?>
    </div>
    <br><br>
    <div class="container">
    <?php 
        $acc = $params['accessories'][0];
        $type = $acc['type'];
        $options = $acc['options'];
        foreach ($options as $i => $option) {
            if ($option == $alpha[$i]) {
                $option = '答案'.$option;
            } 
            echo $alpha[$i].'.&nbsp;&nbsp;'.$option;
            echo '<p style="height:0.2em">&nbsp;</p>';
        }
    ?>
    </div>
    <br><br>
    <div class="container">
        <table style="width:100%; margin: 0px auto;" border=1>
        <tr>
            <td align="center">正确答案</td>
            <td align="center">易错项</td>
            <td align="center">全站正确率</td>
            <td align="center">难度</td>
            <td align="center" width="60%">来源</td>
        </tr>
        <tr>
        <?php
            $answer = $params['correctAnswer'];
            $wrong = $params['mostWrongAnswer'];
        ?>
            <td align="center"><?php echo $alpha[$answer['choice']]; ?></td>
            <td align="center"><?php echo $alpha[$wrong['choice']]; ?></td>
            <td align="center"><?php echo round($params['correctRatio'], 2); ?>%</td>
            <td align="center"><?php echo $params['difficulty']; ?></td>
            <td align="center" width="60%"><?php echo $params['source']; ?></td>
        </tr></table>    
    </div>
    <br><br>
    <div class="container">
    <?php echo '解析:<br><br>'.$params['solution']; ?>
    </div>
    <br><br>
    <!-- Javascript Files -->
    <script src="https://cdn.bootcss.com/jquery/3.2.1/jquery.min.js"></script>
    <script src="https://cdn.bootcss.com/bootstrap/3.3.7/js/bootstrap.min.js"></script>
</body>
</html>
