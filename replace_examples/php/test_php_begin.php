<?php
// MODIFIED: Added strict types declaration and new comment
/**
 * Test file for ReplaceLine at beginning - PHP opening tag.
 * Demonstrates PHP with HTML mixed content.
 */

declare(strict_types=1);

require_once 'vendor/autoload.php';

$title = "Welcome Page";
?>
<!DOCTYPE html>
<html>
<head>
    <title><?php echo $title; ?></title>
</head>
<body>
    <h1>Hello World</h1>
    <?php if (true): ?>
        <p>Condition met</p>
    <?php endif; ?>
</body>
</html>