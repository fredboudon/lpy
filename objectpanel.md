Quelques notes sur l'object panel:

l'object panel a été refait avec des structures Qt. Il se divise comme suit :

## Fichiers

- objectpanel.py : inclut de quoi instancier un panel, des vues, un modèles et un contrôleur.
- objectpannelcommon.py : inclut quelques literals et quelques fonctions communes aux différents composants (notamment la fonction de sanity check des noms. J'aurais pu la mettre dans le contrôleur mais elle est bien là.)
- treeview.py : une vue en arbre du modèle.
- listview.py : une vue en liste du modèle. L'affichage est rendu par un objet de type *QStyledItemDelegate* qui a été sous-classé et réimplémenté.
- treecontroller.py : un contrôleur pour le modèle. Il rassemble peut-être un peu trop de trucs (il devient un peu God Class) mais j'ai l'impression qu'il y avait besoin de pas mal de choses que j'ai mises ici.

Parmi les dialogs et éditeurs:
- objecteditorwidget.py : un QWidget pour instancier l'éditeur d'objets Lpy (ce que j'appelle à beaucoup d'endroits des "lpyresources".) Ce widget peut être embarqué dans le volet droit de l'objectpanel, ou instancié dans un dialog. Notez que suivant l'endroit où il est appelé, il peut y avoir du code pour activer ou désactiver certains boutons.
- objecteditordialog.py : un dialog pour instancier l'objecteditorwidget. 
- renamedialog.py : un dialog pour renommer les items. Il vérifie l'unicité des noms pour le renommage.
- timepointsdialog.py : un dialog pour éditer les timepoints des group-timelines.

## Structure de données

Cet objectpanel a une structure d'arbre. Le modèle de cette structure de données est un QStandardItemModel. Ce modèle se définit comme suit:

- le modèle comporte des items de type QStandardItem.
- chaque item peut être référencé par son index, de type QModelIndex.
- chaque item contient un nombre réduit de données. Ces données sont stockées dans les items du modèle grâce à des rôles. Certains sont des rôles standard de Qt, d'autres sont des rôles customisés créés pour ce cas d'usage. Les rôles customisés sont définis comme literals dans `objectpanelcommon.py`.
  + Qt.DisplayRole : nom d'affichage
  + Qt.DecorationRole : icone d'affichage
  + Qt.BackgroundRole : couleur de fond
  + QT_USERROLE_UUID : un identifiant unique propre à l'item
  + QT_USERROLE_PIXMAP : l'image miniature à afficher dans la listview (et qui est différent de l'icone d'affichage)
- les items peuvent être rangés comme des fils d'autres items (c'est une structure d'arbre). Dans ce cas, il est simplement indiqué que le parent de l'item est un autre item. Si l'item est à la racine de l'arbre, le parent vaut None.
- les items peuvent être des groupes (contiennent d'autres items), des lpyresources (courbe, patch, etc), ou des groupes particuliers dits "group-timelines" qui sont des groupes gérant une seule ressource multipliée autant de fois que nécessaire.

Le modèle QStandardItemModel permet de stocker la structure en arbre et de gérer son affichage. Elle ne permet pas de stocker des données complexes. Pour accéder aux données complexes de chaque item, il faut y accéder dans un dictionnaire python appelé le "store" (c'est un store pattern, somme toute). La valeur qui joue le rôle de clé primaire entre le QStandardItem et le store, c'est l'UUID stocké dans le rôle QT_USERROLE_UUID.

## Store

Le store est un dictionnaire python qui garde toutes les valeurs des objets instanciés. Pour accéder aux valeurs d'un objet, il faut faire appel au store avec la valeur de l'UUID.

```python
uuid: QUuid = item.data(QT_USERROLE_UUID)
values: dict = store[uuid]
```

L'objet retourné (nommé `values` dans l'exemple ci-dessus) est un dictionnaire qui contient les clés suivantes suivant l'objet. Ces clés sont référencées comme literals dans objectpanelcommon.py

- Si l'item est une "lpyresource" :
  + STORE_MANAGER_STR => renvoie l'objet "manager" de la ressource pour l'éditeur
  + STORE_LPYRESOURCE_STR -> renvoie la ressource elle-même (curve, patch, etc)
  + STORE_TIME_STR -> renvoie le timepoint de la ressource si elle est dans un group-timeline, sinon la valeur vaut None.
- Si l'item est un "group-timeline" :
  + STORE_TIMEPOINTS_STR -> renvoie une liste des timepoints
- Sinon (si c'est un groupe normal):
  + le dictionnaire renvoyé est vide `{}`
  
Ainsi, pour continuer l'exemple : 

```python
# supposons que `item` soit un group-timeline
uuid: QUuid = item.data(QT_USERROLE_UUID)
values: dict = store[uuid]
timepoints: list[float] = values[STORE_TIMEPOINTS_STR]

# supposions que `item2` soit une lpyressource dans un group-timeline
uuid2: QUuid = item2.data(QT_USERROLE_UUID)
values2: dict = store[uuid2]
lpyresource: object = values2[STORE_LPYRESOURCE_STR]
manager: AbstractObjectManager = values2[STORE_MANAGER_STR]
time: float = values2[STORE_TIME_STR]
```

Note : j'ai tendance à systématiquement typer mes variables, je trouve que ça aide à la relecture pour être sûr de ce qu'on manipule (avec : `variable: type = valeur`).

## Instanciation

Les widgets et autres items sont instanciés comme suit : 

Dans un objectpanel, il y a:
- un unique store
- un unique modèle
- un uniuqe contrôleur
- un QSplitter qui divise le panel en 2 vues.
  + à gauche, il y a toujours la treeView
  + à droite : 
    * si on clique sur une lpyressource, un objecteditorwidget est affiché et la ressource est chargée.
    * si on clique sur un groupe, le contenu est affiché dans une listView
    * si on clique sur rien, la racine de l'arbre est affiché dans une listView
    * si on sélectionne plusieurs items, rien n'est affiché.

Cela correspond au code dans `class LpyObjectPanelDock`, dans `__init__`.