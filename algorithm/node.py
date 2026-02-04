import math

class ISMCTSNode:
    def __init__(self, parent=None, move=None):
        self.parent = parent
        self.move = move          # Card that led to this node
        self.children = []
        self.visits = 0
        self.wins = 0

    def uct(self, total_visits, c=1.41):
        if self.visits == 0:
            return float("inf")
        return (self.wins / self.visits) + c * math.sqrt(
            math.log(total_visits) / self.visits
        )

    def best_child(self):
        return max(self.children, key=lambda c: c.visits)

    def untried_moves(self, legal_moves):
        tried = {child.move for child in self.children}
        return [m for m in legal_moves if m not in tried]

    def add_child(self, move):
        child = ISMCTSNode(parent=self, move=move)
        self.children.append(child)
        return child