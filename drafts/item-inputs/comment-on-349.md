# Draft comment for issue #349

<!-- cspell:ignore zhang honghao wsbrunson pjordan -->

> Post on <https://github.com/Universal-Commerce-Protocol/ucp/issues/349>
> ("Line items have no field for buyer notes"), which maintainers kept
> open to track this use case when closing #607. Post this before filing
> the proposal, so the proposal does not collide with work already under
> way.

---

Following up on the closing notes on #607 and #915.

On #915 the direction was to refocus around (1) standard optional fields
for common inputs and (2) merchant-specific extensions declared in the
business profile, with a new Enhancement Proposal issue to carry it. I
could not find that issue yet. Is someone drafting it? @zhang-honghao, are
you planning to?

I am interested in one part of this: input that belongs to a specific
line item and that the product cannot be made without. Engraving text, a
monogram, a name and number on a jersey. A few things make that case
different from checkout-level fields such as a gift message:

- The rules differ per product (20 characters on one watch, 3 initials on
  a towel), so a single merchant-level schema does not describe them.
- A Platform needs the rules before a checkout exists, which was
  @wsbrunson's point on #481 about the forced Create → Update → Complete
  flow.
- The value has to reach the Order, which @pjordan's review of #915 noted
  was missing.
- There is often a charge and a longer lead time.

The specification already assumes these products exist. The Return Policy
extension's example marks an engraved item as final sale, but a Platform
has no way to say what to engrave. Food Checkout addressed the same need
for its vertical in #897. The only answer for shopping so far has been to
hand off to embedded checkout (Discussion #27).

I have a draft proposal for a per-item extension that declares inputs on
the catalog variant, carries values on cart and checkout line items, and
records them on the order. It reuses the four input types from #481
(text, choice, boolean, date) so it can share a vocabulary with the
checkout-level work.

Two questions before I file it:

1. Would the Tech Council prefer this as its own proposal, or folded into
   the one requested on #915?
2. Is anyone from a marketplace or merchant with personalized products
   willing to review it? Their per-product rules are the hard part and I
   would rather get them right early.

Happy to collaborate with whoever is already working on this.
