from dataclasses import dataclass

@dataclass(frozen=True)
class CustomerNeed:
    name: str
    product_type: str
    shopping_list: tuple[str, ...]


@dataclass(frozen=True)
class CustomerProfile:
    customer_id: str
    name: str
    age: int
    gender: str
    income_bracket: str
    churned: bool
    marital_status: str
    number_of_children: int
    education_level: str
    occupation: str
    race: str
    disability: bool
    height_cm: int
    customer_needs: tuple[str, ...]
    purchased_alcohol_before: bool
    fitness_level: str
    organic_preference: bool
    total_historical_purchase: float
    avg_purchase_value: float
    shopping_needs: tuple[CustomerNeed, ...]

    def build_persona_summary(self) -> str:
        needs_text = ", ".join(self.customer_needs) or "general shopping"
        shopping_goals = []
        for need in self.shopping_needs:
            goals_text = ", ".join(need.shopping_list)
            shopping_goals.append(
                f"- {need.name} ({need.product_type}): {goals_text}"
            )

        churned_text = "has churned before" if self.churned else "is currently retained"
        alcohol_text = (
            "has previously purchased alcohol"
            if self.purchased_alcohol_before
            else "has not previously purchased alcohol"
        )
        organic_text = (
            "prefers organic options"
            if self.organic_preference
            else "does not prioritize organic options"
        )
        disability_text = (
            "has a disability"
            if self.disability
            else "does not report a disability"
        )

        lines = [
            f"You are shopper {self.name} ({self.customer_id}).",
            (
                f"Profile: {self.age} year old {self.gender}, {self.occupation}, "
                f"{self.income_bracket} income, {self.marital_status}, "
                f"{self.number_of_children} children, education {self.education_level}."
            ),
            (
                f"Customer history: {churned_text}; average purchase value "
                f"{self.avg_purchase_value:.2f}; lifetime purchases "
                f"{self.total_historical_purchase:.2f}."
            ),
            (
                f"Preferences: fitness {self.fitness_level}, {organic_text}, "
                f"{alcohol_text}, needs {needs_text}."
            ),
            (
                f"Additional context: race {self.race}, {disability_text}, "
                f"height {self.height_cm} cm."
            ),
            "Shopping goals:",
            *shopping_goals,
        ]
        return "\n".join(lines)

    def get_target_products(self) -> list[str]:
        targets: list[str] = []
        seen: set[str] = set()
        for need in self.shopping_needs:
            for product_name in need.shopping_list:
                if product_name in seen:
                    continue
                seen.add(product_name)
                targets.append(product_name)
        return targets

    def build_behavioral_directives(self) -> str:
        directives: list[str] = []

        if self.income_bracket == "Low":
            directives.append(
                "You are budget-conscious. Prioritize discounted items and "
                "avoid impulse purchases."
            )
        elif self.income_bracket == "High":
            directives.append(
                "You have high spending power. You appreciate quality and "
                "may consider premium or specialty products near your targets."
            )

        if self.organic_preference:
            directives.append(
                "You strongly prefer organic products. When choosing between "
                "similar items, always favor organic options."
            )

        if self.fitness_level == "Fit":
            directives.append(
                "You are health-focused. You gravitate toward nutritious, "
                "low-sugar, high-protein options."
            )
        elif self.fitness_level == "Unfit":
            directives.append(
                "You prefer convenient, ready-to-eat, and comfort foods."
            )

        if self.churned:
            directives.append(
                "You are an impatient shopper who has left this store before. "
                "Get your items quickly and head to checkout without lingering."
            )

        if self.number_of_children > 0:
            n = self.number_of_children
            directives.append(
                f"You shop for a family with {n} "
                f"{'child' if n == 1 else 'children'}. "
                "Family-sized and kid-friendly products matter to you."
            )

        if self.customer_needs:
            needs_text = ", ".join(self.customer_needs)
            directives.append(
                f"Your core shopping priorities are: {needs_text}."
            )

        if self.purchased_alcohol_before:
            directives.append(
                "You have purchased alcohol before and may pick some up "
                "if you pass by it."
            )

        if self.avg_purchase_value > 0:
            directives.append(
                f"Your typical trip costs around ${self.avg_purchase_value:.2f}."
            )

        if self.disability:
            directives.append(
                "You move carefully and prefer efficient, direct routes "
                "through the store."
            )

        return "\n".join(directives)
