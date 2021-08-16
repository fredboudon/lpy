# Tour d'horizon de TreeView

Classe héritant de QTreeView pour afficher le modèle en arbre.
L'affichage est celui par défaut de Qt. Pour voir un affichage customisé d'une vue, se rendre à ListDelegate dans treecontroller.py qui est utilisé dans ListView.

## class TreeView

### champs

- panelManager: pointeur vers le panelManager (il n'est pas utilisé, reliquat)
- selectedIndexChanged: signal à lancer quand la sélection change. Il permet d'informer l'objectpanel pour mettre à jour le panel de droite.
- controller: le pointeur vers le contrôleur


### methods

- __init__ : juste les fonctions d'initialisation. On set le model, le delegate, des options, et le callback pour le menu contextuel.
- un paquet de fonctions pas utilisées: `getItemsFromActiveGroup, getChildrenTreeDemo, getChildrenTree, getObjects, getObjectsCopy, setObjects, appendObjects, appendObject`
        + ces fonctions doivent être supprimées (elles n'ont rien à faire là), elles devraient être réimplémentées côté contrôleur comme il se doit. Elles ne marchent pas à l'heure actuelle.
- `selectionChanged`: callback appelée quand la sélection change (clic, flèche du clavier, MAJ-clic etc.). Réimplémentée pour trigger le signal `selectedIndexChanged`.
- `createItemFromMenu`: callback appelée par le menu contextuel pour dépaqueter les données envoyeés par la QAction. J'aurais pu la mettre directement dans la fonction `createItem` du contrôleur mais elle est déjà assez massive comme ça, c'est plus raisonnable de la mettre ici. Le passage de données se fait avec les QAction Data **(voir "Note : passage de paramètres comme data de QAction" dans treecontroller.md)**.
- `contextMenuRequest`: callback appelée quand on fait un clic droit. 
  + on vérifie sur quoi on a cliqué avec les bool `isClickingOnGroupOrBackground, isClickingOnSingleResource, isClickingOnGroupTimeline, isClickingOnResourceTimeline`
  + on définit toutes les actions possibles dans le dict `menuActions`
  + on sélectionne les actions pertinentes en ajoutant les bonnes menuActions[...] dans la liste `selectedActions`.
  + pour passer des paramètres aux callbacks des QActions on utilise les QAction Data **(voir "Note : passage de paramètres comme data de QAction" dans treecontroller.md)**