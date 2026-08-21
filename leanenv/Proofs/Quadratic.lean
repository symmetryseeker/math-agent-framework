import Mathlib

/-!
# Quadratic extrema — Lean 4 + Mathlib 真证明
待编译验证：f(x) = a·x + b·x² 在 x* = -a/(2b) 处是局部极值。
-/

/-- f'(x) = a + 2·b·x — 一阶导数公式（FOC 的符号基础） -/
theorem quadratic_first_deriv {a b : ℝ} :
    deriv (fun x : ℝ => a * x + b * x ^ 2) = fun x => a + 2 * b * x := by
  funext x
  simp [deriv_add, deriv_const_mul, deriv_pow, deriv_id'']
  ring

/-- b > 0 时，x* = -a/(2b) 是 f 的（全局，因而局部）最小值。 -/
theorem quadratic_minimum_unique {a b : ℝ} (hbpos : 0 < b) :
    IsLocalMin (fun x => a * x + b * x ^ 2) (-a / (2 * b)) := by
  -- 配方：f(x) - f(x*) = b·(x - x*)²
  have hsq : ∀ x : ℝ,
      a * x + b * x ^ 2 = b * (x + a / (2 * b)) ^ 2 + (a * (-a / (2 * b)) + b * (-a / (2 * b)) ^ 2) := by
    intro x
    ring
  -- 全局不等式 f(x*) ≤ f(x) 对一切 x 成立
  have hglob : ∀ x : ℝ,
      a * (-a / (2 * b)) + b * (-a / (2 * b)) ^ 2 ≤ a * x + b * x ^ 2 := by
    intro x
    rw [hsq x]
    have : 0 ≤ b * (x + a / (2 * b)) ^ 2 := by
      exact mul_nonneg (le_of_lt hbpos) (sq_nonneg (x + a / (2 * b)))
    linarith
  -- 全局最小 → 局部最小
  exact IsGlobalMin.isLocalMin ⟨by intro x; exact hglob x⟩

/-- b < 0 时，x* = -a/(2b) 是 f 的（全局，因而局部）最大值。 -/
theorem quadratic_maximum_unique {a b : ℝ} (hbneg : b < 0) :
    IsLocalMax (fun x => a * x + b * x ^ 2) (-a / (2 * b)) := by
  have hsq : ∀ x : ℝ,
      a * x + b * x ^ 2 = b * (x + a / (2 * b)) ^ 2 + (a * (-a / (2 * b)) + b * (-a / (2 * b)) ^ 2) := by
    intro x
    ring
  have hglob : ∀ x : ℝ,
      a * x + b * x ^ 2 ≤ a * (-a / (2 * b)) + b * (-a / (2 * b)) ^ 2 := by
    intro x
    rw [hsq x]
    have : b * (x + a / (2 * b)) ^ 2 ≤ 0 := by
      exact mul_nonpos_of_nonpos_of_nonneg (le_of_lt hbneg) (sq_nonneg (x + a / (2 * b)))
    linarith
  exact IsGlobalMax.isLocalMax ⟨by intro x; exact hglob x⟩
