<?php
session_start();
require_once("connexion.php");

if (!isset($_SESSION['login']) || empty($_SESSION['panier'])) { header("Location: afficher_evenements.php"); exit(); }

$success = false;
$error_msg = "";

try {
	$mysqlConnection->beginTransaction();
	
	foreach ($_SESSION['panier'] as $id_ev) {
		
		
		$stmt = $mysqlConnection->prepare("SELECT * FROM event WHERE id_event = :id");
		$stmt->execute([':id' => $id_ev]);
		$ev = $stmt->fetch(PDO::FETCH_ASSOC);
		
		if ($ev) {
			
			if ($ev['places_disponibles'] <= 0) { 
				throw new Exception("Complet pour : " . $ev['titre']); 
			}
			
			$prix_final = ($_SESSION['statut'] === 'Etudiant') ? $ev['prix_etudiant'] : $ev['prix_public'];
			
		
			$ins = $mysqlConnection->prepare("INSERT INTO inscription (id_utilisateur, id_evenement, date_inscription, prix_applique, statut_inscription) VALUES (?, ?, NOW(), ?, 'Confirme')");
			$ins->execute([$_SESSION['id_user'], $ev['id_event'], $prix_final]);
			
			
			$up = $mysqlConnection->prepare("UPDATE event SET places_disponibles = places_disponibles - 1 WHERE id_event = ?");
			$up->execute([$ev['id_event']]);
		}
	}
	
	$mysqlConnection->commit();
	unset($_SESSION['panier']); 
	$success = true;
	
} catch (Exception $e) {
	$mysqlConnection->rollBack(); 
	$error_msg = $e->getMessage();
}
?>
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Confirmation</title>
<link rel="stylesheet" href="pfm.css">
</head>
<body>
<?php include("menu.php"); ?>
<div style="max-width: 600px; margin: 30px auto; background: white; padding: 25px; border-radius: 8px;">
<?php if ($success): ?>
<h2 style='color:green;'>✔️ Transactions enregistrées  !</h2>
<p>Inscriptions validées.</p>
<?php else: ?>
<h2 style='color:red;'>❌ Échec de la transaction</h2>
<p>Erreur : <?php echo htmlspecialchars($error_msg); ?></p>
<?php endif; ?>
<a href="afficher_evenements.php">Retour au catalogue</a>
</div>
</body>
</html>
