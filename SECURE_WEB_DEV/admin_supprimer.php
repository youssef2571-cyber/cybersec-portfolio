<?php
session_start();
require_once("connexion.php");
if (!isset($_SESSION['role']) || $_SESSION['role'] !== 'admin') { header("Location: login.php"); exit(); }

$id = $_GET['id'] ?? null;
if ($id) {
	$stmt = $mysqlConnection->prepare("DELETE FROM event WHERE id_event = ?");
	$stmt->execute([$id]);
}
header("Location: admin_dashboard.php");
exit();
?>
