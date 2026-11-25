# Draft comment for issue #349

<!-- cspell:ignore hemanth zhang honghao wsbrunson pjordan -->

> Post on <https://github.com/Universal-Commerce-Protocol/ucp/issues/349>
> ("Line items have no field for buyer notes"). Post this when filing the
> proposal, so the people who worked on this before hear about it from
> you.

---

@hemanth, @zhang-honghao: I have been working on the per-item side of
this problem and am filing an Enhancement Proposal for it. I wanted both
of you to hear it here first, since it builds on your work.

@hemanth, this issue and your two pull requests (#402, #607) made the
case that buyer input belongs on the line item. What I have builds on
that. @zhang-honghao, #915 added the idea that the business declares what
it needs and marks it required. Both are credited in the proposal. If you
are writing the Enhancement Proposal the maintainers asked for on #915,
tell me and I will reference it from mine.

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
Two questions:

1. @hemanth, @zhang-honghao, would either of you like to co-author or
   review? You know the earlier discussion better than anyone.
2. Would the Tech Council prefer the checkout-level fields in the same
   proposal, or kept separate?
