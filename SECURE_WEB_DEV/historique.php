<?php
session_start();
require_once("connexion.php");
if (!isset($_SESSION['login'])) { 
	header("Location: login.php"); 
	exit(); 
}

$id_user = $_SESSION['id_user'];


$sql = "SELECT event.titre, event.date_event, event.lieu, inscription.date_inscription, inscription.prix_applique, inscription.statut_inscription FROM inscription INNER JOIN event ON inscription.id_evenement = event.id_event 
WHERE inscription.id_utilisateur = :id_user ORDER BY inscription.date_inscription DESC";

$stmt = $mysqlConnection->prepare($sql);
$stmt->execute([':id_user' => $id_user]);
$historique = $stmt->fetchAll(PDO::FETCH_ASSOC);
?>
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Mon Historique</title>
<link rel="stylesheet" href="pfm.css">
</head>
<body>
<?php include("menu.php"); ?>

<div class="container">
<h2>📜 Historique de mes inscriptions</h2>

<?php if (empty($historique)): ?>
<p>Vous n'avez encore participé à aucun événement.</p>
<a href="afficher_evenements.php"><button>Découvrir le catalogue</button></a>
<?php else: ?>
<table border="1" cellpadding="10" style="width:100%; border-collapse:collapse;">
<tr style="background:#34495e; color:white;">
<th>Événement</th>
<th>Lieu</th>
<th>Date de l'événement</th>
<th>Date de réservation</th>
<th>Prix payé</th>
<th>Statut</th>
</tr>
<?php foreach ($historique as $ligne): ?>
<tr>
<td><?php echo htmlspecialchars($ligne['titre']); ?></td>
<td><?php echo htmlspecialchars($ligne['lieu']); ?></td>
<td style="white-space: nowrap;"><?php echo htmlspecialchars($ligne['date_event']); ?></td>
<td style="white-space: nowrap;"><?php echo htmlspecialchars($ligne['date_inscription']); ?></td>
<td><strong><?php echo htmlspecialchars($ligne['prix_applique']); ?> DH</strong></td>
<td style='color:green; font-weight:bold;'><?php echo htmlspecialchars($ligne['statut_inscription']); ?></td>
</tr>
<?php endforeach; ?>
</table>
<?php endif; ?>
</div>
</body>
</html>
