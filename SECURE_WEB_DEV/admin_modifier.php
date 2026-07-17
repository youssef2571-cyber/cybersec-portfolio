<?php
session_start();
require_once("connexion.php");
if (!isset($_SESSION['role']) || $_SESSION['role'] !== 'admin') { header("Location: login.php"); exit(); }

$id = $_GET['id'] ?? null;
if (!$id) { header("Location: admin_dashboard.php"); exit(); }

if ($_SERVER["REQUEST_METHOD"] == "POST") {
	try {
		$sql = "UPDATE event SET titre=:t, description=:d, date_event=:dt, lieu=:l, prix_etudiant=:pe, prix_public=:pp, places_disponibles=:pl WHERE id_event=:id";
		$stmt = $mysqlConnection->prepare($sql);
		$stmt->execute([':t' => $_POST['titre'], ':d' => $_POST['description'], ':dt' => $_POST['date_event'], ':l' => $_POST['lieu'], ':pe' => $_POST['prix_etudiant'], ':pp' => $_POST['prix_public'], ':pl' => $_POST['places_disponibles'], ':id' => $id]);
		header("Location: admin_dashboard.php"); exit();
	} catch (PDOException $e) { echo "<p style='color:red;'>Erreur : " . $e->getMessage() . "</p>"; }
}

$stmt = $mysqlConnection->prepare("SELECT * FROM event WHERE id_event = ?");
$stmt->execute([$id]);
$ev = $stmt->fetch(PDO::FETCH_ASSOC);
if (!$ev) { die("Introuvable."); }
?>
<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><title>Modifier</title><link rel="stylesheet" href="pfm.css"></head>
<body>
<?php include("menu.php"); ?>
<div style="max-width: 700px; margin: 30px auto; background: white; padding: 25px;">
<h2>Modifier l'événement</h2>
<form method="POST" action="admin_modifier.php?id=<?php echo $id; ?>">
Titre : <input type="text" name="titre" value="<?php echo htmlspecialchars($ev['titre']); ?>" required><br><br>
Description : <br><textarea name="description" rows="3" style="width:100%;"><?php echo htmlspecialchars($ev['description']); ?></textarea><br><br>
Date : <input type="date" name="date_event" value="<?php echo htmlspecialchars($ev['date_event']); ?>" required><br><br>
Lieu : <input type="text" name="lieu" value="<?php echo htmlspecialchars($ev['lieu']); ?>" required><br><br>
Prix Étudiant (DH) : <input type="number" step="0.01" name="prix_etudiant" value="<?php echo htmlspecialchars($ev['prix_etudiant']); ?>" required><br><br>
Prix Public (DH) : <input type="number" step="0.01" name="prix_public" value="<?php echo htmlspecialchars($ev['prix_public']); ?>" required><br><br>
Places disponibles : <input type="number" name="places_disponibles" value="<?php echo htmlspecialchars($ev['places_disponibles']); ?>" required><br><br>
<button type="submit">Mettre à jour</button> <a href="admin_dashboard.php" style="margin-left:15px;">Annuler</a>
</form>
</div>
</body>
</html>
