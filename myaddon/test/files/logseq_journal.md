- ## Log
	- 15:37: Développement Loki
		- 15:37: Amélioration [[PanLog]]
			- 15:37: Comparaison avec la database pour détecter les cartes déjà triées.
				- *Note*: La fonction `generate_database()` renvoi des données converti en HTML. Pas idéal pour le traitement.
			- 16:45: Pause
			- 17:03: [Annulé] Changement de la fonction `generate_database()` pour renvoyer du texte brut.
				- *Note*: Avoir du HTML dans la database fait sens car sa création se base justement sur une conversion en HTML et un parsing avec Beautifull Soup.
			- 17:12: [Annulé] Extraire une fonction pour convertir un fichier en HTML. Cette fonction pourra être utilisé comparer du texte brut avec la database.
			- 17:19: Changer la fonction de comparaison avec la database en ajoutant deux étapes:
				- 17:19: Utiliser la même fonction que la création de la database mais avec un seul fichier.
				- 17:40: Ecriture des données extraites du Log dans un fichier Markdown avec le même format que le reste de la database.
			- 19:05: Fin de journée
- ## Tasks
	- Unifier la génération de database entre le plugin Anki et [[Panlog]].
	- Ajouter une condition dans la comparaison du niveau de tabulation pour ajouter des listes.
- ## Pour demain
	- Maintenant on a:
		- LogSeq -> Markdown
		- Markdown -> HTML (pour la comparaison database)
		- HTML -> Anki
	- Il faut maintenant HTML -> Markdown
	- Résumé du workflow:
		- PanLog:
			- LogSeq -> Markdown
			- Markdown -> HTML (pour comparaison)
			- HTML -> Markdown
- ## Notes
	- Hopla une deuxième carte normalement #Anki #ToStore
		- C'est une réponse hopla
		- Une deuxième ligne.
	- Un test de carte avec code nested #Anki #ToStore
		- ``` c++ 
		  // Fibonacci Series using Space Optimized Method
		  #include <bits/stdc++.h>
		  using namespace std;
		   
		  int fib(int n)
		  {
		      int a = 0, b = 1, c, i;
		      if (n == 0)
		          return a;
		      for (i = 2; i <= n; i++) {
		          c = a + b;
		          a = b;
		          b = c;
		      }
		      return b;
		  }
		   
		  // Driver code
		  int main()
		  {
		      int n = 9;
		   
		      cout << fib(n);
		      return 0;
		  }
		   
		  // This code is contributed by Code_Mech
		  ```
		- Avec du texte après.
		-