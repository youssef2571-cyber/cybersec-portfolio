<?php
session_start();
require_once("connexion.php");

if (!isset($_SESSION['login'])) { header("Location: login.php"); exit(); }

$events_panier = [];
$total = 0;

if (!empty($_SESSION['panier'])) {
	foreach ($_SESSION['panier'] as $id_ev) {
		
		$stmt = $mysqlConnection->prepare("SELECT * FROM event WHERE id_event = :id");
		$stmt->execute([':id' => $id_ev]);
		$event = $stmt->fetch(PDO::FETCH_ASSOC);
		
		
		if ($event) {
			$events_panier[] = $event;
		}
	}
}
?>
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Mon Panier</title>
<link rel="stylesheet" href="pfm.css">
</head>
<body>
<?php include("menu.php"); ?>
<div style="max-width: 900px; margin: 30px auto; background: white; padding: 25px; border-radius: 8px;">
<h2>Mon Panier</h2>
<?php if(empty($events_panier)): ?>
<p>Panier vide.</p>
<?php else: ?>
<table border="1" cellpadding="10" style="width:100%; border-collapse:collapse;">
<tr style="background:#ecf0f1;"><th>Événement</th><th>Date</th><th>Tarif Appliqué</th></tr>
<?php foreach($events_panier as $ev): 
$prix = ($_SESSION['statut'] === 'Etudiant') ? $ev['prix_etudiant'] : $ev['prix_public'];
$total += $prix;
?>
<tr>
<td><?php echo htmlspecialchars($ev['titre']); ?></td>
<td><?php echo htmlspecialchars($ev['date_event']); ?></td>
<td><strong><?php echo $prix; ?> DH</strong></td>
</tr>
<?php endforeach; ?>
<tr>
<td colspan="2" align="right"><strong>Total :</strong></td>
<td><strong><?php echo $total; ?> DH</strong></td>
</tr>
</table>
<br>
<form method="POST" action="confirmer_panier.php">
<button type="submit" style="width:100%; padding:15px; background:#27ae60; color:white; border:none; font-weight:bold; cursor:pointer;">Confirmer mes réservations</button>
</form>
<?php endif; ?>
</div>
</body>
</html>
