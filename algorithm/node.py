import math

class ISMCTSNode:
    def __init__(self, parent = None, move = None):
        self.parent = parent
        self.move = move # the card that let to this node
        self.children = []
        self.visits = 0
        self.wins = 0
        self.eligible_visits = 0 # how many times a move was legal

    def uct(self, total_visits, c = math.sqrt(2)):
        """returns the result of applying the uct formula to the tested moves.

        uct is a formula called upper confidence bound applied to trees, modified to fit the ISMCTS algorithm.
        (modification to fit ismcts: using total times a child node was eligible instead of total times it was visited)"""
        if self.visits == 0:
            return float("inf")
        if self.parent is None:
            total_eligible = self.eligible_visits if self.eligible_visits > 0 else 1
        else:
            total_eligible = self.eligible_visits if self.eligible_visits > 0 else 1
        return (self.wins / self.visits) + c * math.sqrt(math.log(total_eligible) / self.visits)

    def best_child(self, c=math.sqrt(2)):
        """select child with highest UCT value"""
        return max(self.children, key=lambda child: child.uct(c))

    # manage moves

    def untried_moves(self, legal_moves):
        """given a list of legal moves, return unexplored moves"""
        tried = {child.move for child in self.children}
        return [m for m in legal_moves if m not in tried]

    def add_child(self, move):
        """returns a new child node for a move after adding it."""
        child = ISMCTSNode(parent = self, move = move)
        self.children.append(child)
        return child
