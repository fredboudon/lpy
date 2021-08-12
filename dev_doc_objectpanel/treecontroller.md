Tour d'horizon de TreeController

Classe servant de contrôleur pour le modèle QStandardItemModel.

Ses fonctions vont en fait beaucoup plus loin que ça, mais il gère tout ce qui a attrait au modèle et aux ressources (donc au store, puisque le modèle représente la structure d'arbre, et le store stocke les objets pythons complexe, le lien entre les deux étant fait par leurs UUID.)

## Quelques mots sur les Delegate

Qt fonctionne non pas en Modèle-Vue-Contrôleur, mais en Modèle-Vue-Delegate. Dans leur mode de fonctionnement, le Delegate est un objet qui sert non seulement à afficher les éléments du modèle, mais aussi à éditer les éléments du modèle.

Là où c'est ennuyeux c'est que c'est le Delegate qui capture les signaux Qt comme le double-clic, l'appui sur la touche Entrée, etc. pour appeler l'éditeur. J'ai donc décidé de créer des Delegates et de les placer au niveau du contrôleur, quand bien même ils peuvent avoir des fonctions de visualisation aussi. J'ai fait cela parce que le delegate doit avoir accès à pas mal de fonctions liées au contrôleur.

## class ListDelegate

Classe servant à l'affichage des items dans la liste.
Je l'ai mise dans le fichier TreeController parce que c'est le contrôleur qui l'instancie.

Méthodes réimplémentées :

- createEditor : est appelée sur signal d'édition (double-clic, entrée). Réimplémenté pour ne rien faire, et lever un signal Qt à la place, qui est attrapé par le contrôleur.

- paint : fonction qui doit afficher les items du modèle. Réimplémentée pour afficher des carrés, des rectangles, etc. Les éléments à afficher sont récupérés avec les Rôles des QStandardItem ( par ex. `index.data(Qt.DisplayRole)` renvoie une string avec le nom de l'item).

- sizeHint : fonction qui doit renvoyer la taille de chaque objet à afficher. J'ai décidé d'afficher des mosaïques carrées, elle renvoie donc simplement `QSize(GRID_WIDTH_PX, GRID_HEIGHT_PX)`.

## class TreeDelegate

Classe servant à l'affichage des items dans l'arbre.
Je l'ai mise dans le fichier TreeController parce que c'est le contrôleur qui l'instancie.

Elle hérite de QStyledItemDelegate pour afficher les rôles par défaut (Qt.DisplayRole => affiche le texte, Qt.BackgroundRole => met une couleur en background...). Sa fonction paint n'est pas réimplémentée, j'ai gardé l'affichage par défaut.

Méthodes réimplémentées :

- createEditor : est appelée sur signal d'édition (double-clic, entrée). Réimplémenté pour ne rien faire, et lever un signal Qt à la place, qui est attrapé par le contrôleur.

Autrement dit ce Delegate ne sert qu'à attraper le signal d'édition pour le renvoyer dans un autre signal qu'on peut attraper avec le contrôleur.

## class TreeController

### Champs

cette classe stocke :

-    model: QStandardItemModel = le modèle
-    store: dict = le store
-    treeDelegate: TreeDelegate = le delegate pour la vue en arbre (puisqu'il renvoie un signal pour demander l'édition, il faut le connecter)
-    listDelegate: ListDelegate = le delegate pour la vue en liste (puisqu'il renvoie un signal pour demander l'édition, il faut le connecter)
-    uuidEditorOpen: list[QUuid] = la liste des éditeurs ouverts avec certaines ressources. Ca permet de cacher l'éditeur dans le volet de droite s'il est déjà ouvert
-    editorCreated: pyqtSignal = pyqtSignal(list) quand on crée un éditeur, on met à jour la liste des éditeurs ouverts
-    editorClosed: pyqtSignal = pyqtSignal(list) quand on détruit un éditeur, on met à jour la liste des éditeusr ouverts

### Méthodes

#### Note : passage de paramètres comme data de QAction

Beaucoup de méthodes commencent avec ces lignes :

```python
if not isinstance(index, QModelIndex):
    index: QModelIndex = QObject.sender(self).data()
```

Explication : les méthodes commençant avec ces lignes peuvent être appelées par le menu contextuel (clic droit). Dans ce cas, lors de la création de la QAction pour appeler cette fonction, la fonction est appelée comme une callback sans paramètres, et on charge des paramètres *dans la QAction* avec `setData`. (voir méthode `contextMenuRequest` dans `TreeView`). Par exemple : 

```python
menuActions["Clone"] = QAction("Clone", self)
menuActions["Clone"].setData(clickedIndex) #paramètre passé en tant que "data" de la QAction
menuActions["Clone"].triggered.connect(self.controller.cloneItem) # callback enregistrée sans "paramètre de fonction".
```

Ces deux lignes permettent d'appeler la fonction avec un paramètre vide (en l'ocurrence avec `index = None`), puis de récupérer le paramètre envoyé par la QAction. C'est ainsi que Qt permet d'appeler des fonctions comme callbacks avec des paramètres.

#### les méthodes

- createExampleObjects : pour du debug. Permet de créer rapidement plusieurs items pour tester.
- createItem : crée un item dans le modèle, et crée une entrée dans le store pour l'UUID de cet item. Y'a 3000 paramètres dedans mais c'est pour rester logique avec la façon dont elle a été conçue. Quand on l'appelle, elle renvoie le QStandardItem créé **et** elle garantit que le store contient l'enregistrement associé.
- cloneItem : clone un item et tous ses sous-items.
- isLpyResource, isGroupTimeline : tester facilement ce qu'est un item du model (il appelle le store pour vérifier ce qu'il y a dedans. On fait ça *très* souvent alors j'ai fait des petites fonctions pour.)
- createGroupTimeline : crée un group-timeline à partir d'une ressource
- editTimepoints : crée un dialog pour éditer les paramètres du group-timeline.
- createEditorWidget : crée un widget d'édition pour le *manager* donné et le renvoie. Utile puisque parfois l'éditeur est créé en widget pour le volet de droite, parfois pour un dialog.
- createEditorDialog : crée un dialog dans lequel on met un widget d'édition. Il log les dialogs ouverts dans une liste de QUuid pour savoir lesquels sont déjà ouverts.
- dialogClosedConnect : callback appelée quand on ferme un dialog pour mettre à jour la liste des dialogs ouverts.
- renameItem : ouvre un dialog pour renommer un item. Le renommage vérifie que le nom est unique (sécurité pour quand on l'exporte en dict avec les noms pour clés)
- deleteItemList : supprime les items sélectionnés du modèle (ça peut être plusieurs items sélectionnés en maintenant CTRL)
- saveItem : callback pour mettre à jour la valeur dans le store d'un item.
- exportStore : crée un dict contenant les items de façon hiérarchique pour être utilisé dans Lpy.
