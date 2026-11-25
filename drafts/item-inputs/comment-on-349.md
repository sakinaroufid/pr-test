# Draft comment for issue #349

<!-- cspell:ignore hemanth zhang honghao wsbrunson pjordan -->

> Post on <https://github.com/Universal-Commerce-Protocol/ucp/issues/349>
> ("Line items have no field for buyer notes"). Post this and wait for
> replies before filing the proposal, so it adds to the work already done
> here and does not get ahead of anyone.

---

@hemanth, @zhang-honghao: I have been working on the per-item side of
this problem and want to check with both of you before I file anything.

@hemanth, this issue and your two pull requests (#402, #607) made the
case that buyer input belongs on the line item. What I have builds on
that. @zhang-honghao, #915 added the idea that the business declares what
it needs and marks it required, and the maintainers asked for a new
Enhancement Proposal in the direction set out there. Are you writing
it? If you are, I would like to contribute to yours. I do not want to open
a second one beside it.

What I have is narrower than #915. It covers input that belongs to one
line item and that the product cannot be made without: engraving text, a
monogram, a name and number on a jersey. Four things about that case led
me to a per-product design:

- The rules differ per product (20 characters on one watch, 3 initials on
  a towel), so they are declared on the catalog variant.
- A Platform needs the rules before a checkout exists, which was
  @wsbrunson's point on #481 about the forced Create → Update → Complete
  flow.
- The answer has to reach the Order, which @pjordan's review of #915
  raised.
- There is often a charge and a longer lead time.

It reuses the four input types from Shopify's #481 (text, choice,
boolean, date), so the per-item and checkout-level work can share one
vocabulary. Checkout-level fields such as gift messages and delivery
instructions are outside it and stay with the #915 direction.

I have draft schemas and a specification page with validated examples.
Three questions:

1. @zhang-honghao, would you prefer to fold this into your proposal, or
   have it filed as a companion that references yours?
2. @hemanth, would you like to co-author? The line-item approach started
   with this issue.
3. Would the Tech Council prefer one proposal covering both scopes, or
   two?

I will hold off filing until I hear back here.
