<?php
session_start();
require_once("connexion.php");

if (!isset($_SESSION['login'])) { header("Location: login.php"); exit(); }
$ville_cookie = $_COOKIE['ville'] ?? "Non définie";

if (isset($_GET['action']) && $_GET['action'] === 'reserver' && isset($_GET['id_ev'])) {
	$id_ev = (int)$_GET['id_ev'];
	if (!isset($_SESSION['panier'])) { $_SESSION['panier'] = []; }
	if (!in_array($id_ev, $_SESSION['panier'])) { $_SESSION['panier'][] = $id_ev; }
	header("Location: afficher_evenements.php?success=1");
	exit();
}
?>
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Catalogue</title>
<link rel="stylesheet" href="pfm.css">
</head>
<body>
<?php include("menu.php"); ?>
<div style="max-width: 900px; margin: 30px auto; background: white; padding: 25px; border-radius: 8px;">
<h1>Catalogue (Ville : <?php echo htmlspecialchars($ville_cookie); ?>)</h1>
<?php if(isset($_GET['success'])): ?><p style="color:green; font-weight:bold;">✔️ Ajouté au panier !</p><?php endif; ?>

<table border="1" cellpadding="10" style="width:100%; border-collapse:collapse;">
<tr style="background:#ecf0f1;"><th>Titre</th><th>Description</th><th>Date</th><th>Lieu</th><th>Tarif</th><th>Action</th></tr>
<?php
$stmt = $mysqlConnection->prepare("SELECT * FROM event WHERE lieu = :lieu ORDER BY date_event ASC");
$stmt->bindValue(':lieu', $ville_cookie, PDO::PARAM_STR);
$stmt->execute();
while ($event = $stmt->fetch(PDO::FETCH_ASSOC)) {
	$prix = ($_SESSION['statut'] === 'Etudiant') ? $event['prix_etudiant'] : $event['prix_public'];
	echo "<tr>";
	echo "<td>" . htmlspecialchars($event['titre']) . "</td>";
	echo "<td>" . htmlspecialchars($event['description']) . "</td>";
	echo "<td>" . htmlspecialchars($event['date_event']) . "</td>";
	echo "<td>" . htmlspecialchars($event['lieu']) . "</td>";
	echo "<td>" . $prix . " DH</td>";
	echo "<td><a href='afficher_evenements.php?action=reserver&id_ev=" . $event['id_event'] . "'><button style='background:#3498db; color:white; border:none; padding:5px 10px; cursor:pointer;'>Réserver</button></a></td>";
	echo "</tr>";
}
?>
</table>
</div>
</body>
</html>
