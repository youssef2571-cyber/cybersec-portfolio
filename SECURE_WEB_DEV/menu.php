<?php
if (session_status() == PHP_SESSION_NONE) {
	session_start();
}
?>
<nav>
<?php if (isset($_SESSION['login'])): ?>
<a href="afficher_evenements.php">📅 Catalogue Événements</a>
<a href="panier.php">🛒 Mon Panier (<?php echo isset($_SESSION['panier']) ? count($_SESSION['panier']) : 0; ?>)</a>

<?php if (isset($_SESSION['role']) && $_SESSION['role'] === 'admin'): ?>
<a href="admin_dashboard.php" style="color: #ffcb05;">⚙️ Espace Admin</a>
</style>
<?php endif; ?>
<a href="historique.php">📜 Mon Historique</a>
<a href="deconnexion.php" style="color: #e74c3c;">❌ Déconnexion (<?php echo htmlspecialchars($_SESSION['login']); ?>)</a>
<?php else: ?>
<a href="login.php">🔑 Se Connecter</a>
<a href="inscription.html">📝 S'inscrire (Créer un compte)</a>
<?php endif; ?>
</nav>
