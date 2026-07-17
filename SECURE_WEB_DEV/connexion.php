<?php
// Configuration des paramètres de connexion à la base de données
$dsn = 'mysql:host=localhost;dbname=eventmanagement;charset=utf8';
$user = 'root';
$password = ''; 

try {
    // Création de l'instance PDO et affectation à la variable globale $mysqlConnection
    $mysqlConnection = new PDO($dsn, $user, $password);
    
    // Configuration de PDO pour lever des exceptions en cas d'erreur SQL
    $mysqlConnection->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
}
catch (PDOException $e) {
    // Interception de l'erreur et arrêt du script en cas d'échec de liaison
    echo "Erreur de connexion : " . $e->getMessage() . "<br/>";
    exit();
}
?>
