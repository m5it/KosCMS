<!DOCTYPE html>
<html>
<head>
    <title>PHP Middle Test</title>
</head>
<body>
    <?php
    // PHP block in middle of HTML
    $users = ['Alice', 'Bob', 'Charlie', 'MODIFIED'];
    $count = count($users);
    ?>
    
    <h2>User List (<?php echo $count; ?> users)</h2>
    <ul>
        <?php foreach ($users as $user): ?>
            <li><?php echo htmlspecialchars($user); ?></li>
        <?php endforeach; ?>
    </ul>
    
    <?php
    // Another PHP block
    $message = "Hello from PHP!";
    echo "<p>$message</p>";
    ?>
</body>
</html>