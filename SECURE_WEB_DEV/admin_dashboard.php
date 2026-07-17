<?php
session_start();
require_once("connexion.php");
if (!isset($_SESSION['role']) || $_SESSION['role'] !== 'admin') { header("Location: login.php"); exit(); }
?>
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Administration</title>
<link rel="stylesheet" href="pfm.css">
</head>
<body>
<?php include("menu.php"); ?>
<div style="max-width: 1000px; margin: 30px auto; background: white; padding: 25px; border-radius: 8px;">
<h2>⚙️ Administration Globale</h2>
<a href="admin_ajouter.php"><button style="margin-bottom:15px; background:#2ecc71; color:white; padding:10px 15px; border:none; cursor:pointer; font-weight:bold;">+ Nouvel événement</button></a>

<table border="1" cellpadding="10" style="width:100%; border-collapse:collapse;">
<tr style="background:#34495e; color:white;">
<th>Titre</th><th>Date</th><th>Lieu</th><th>Prix (Etud / Pub)</th><th>Places</th><th>Actions</th>
</tr>
<?php
$stmt = $mysqlConnection->query("SELECT * FROM event ORDER BY date_event ASC");
while ($ev = $stmt->fetch(PDO::FETCH_ASSOC)) {
	echo "<tr>";
	echo "<td>" . htmlspecialchars($ev['titre']) . "</td>";
	echo "<td>" . htmlspecialchars($ev['date_event']) . "</td>";
	echo "<td>" . htmlspecialchars($ev['lieu']) . "</td>";
	echo "<td>" . htmlspecialchars($ev['prix_etudiant']) . " / " . htmlspecialchars($ev['prix_public']) . " DH</td>";
	echo "<td>" . htmlspecialchars($ev['places_disponibles']) . "</td>";
	echo "<td>
	<a href='admin_modifier.php?id=" . $ev['id_event'] . "' style='color:#f39c12; text-decoration:none; font-weight:bold;'>✏️ Modifier</a> | 
	<a href='admin_supprimer.php?id=" . $ev['id_event'] . "' onclick='return confirm(\"Supprimer cet événement ?\");' style='color:#e74c3c; text-decoration:none; font-weight:bold;'>🗑️ Supprimer</a>
	</td>";
	echo "</tr>";
}
?>
</table>
</div>
</body>
</html>
