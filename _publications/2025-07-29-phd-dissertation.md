---
title: "Optimizing Web Applications Using Declarative Software Rewriting"
collection: dissertation
category: dissertation
permalink: /publication/2025-07-29-satya-dissertation
excerpt: 'We present Declarative Software Rewriting as an effective technique for automated software refactoring where changes are intrusive and span multiple files. We demonstrate the application of a declarative re-writing approach to performance and security optimization in the following contributions: (i) automatic migration from synchronous to asynchronous JavaScript APIs, (ii) increasing the responsiveness of web applications by introducing lazy loading, (iii) remediating superfluous re-rendering in React applications, and (iv) rewriting WebAssembly binaries to mitigate security vulnerabilities.' 
date: 2021-10-15
venue: ''
paperurl: 'http://spitfiresatya.github.io/files/papers/satya_dissertation.pdf'
citation: 'Satyajit Gokhale. <i>Optimizing Web Applications Using Declarative Software Rewriting</i>. Doctoral dissertation, Northeastern University (July 2025), 161 pages.'
bibtex: |
  @phdthesis{gokhale2025rewriting,
    author = {Gokhale, Satyajit},
    title  = {Optimizing Web Applications Using Declarative Software Rewriting},
    school = {Northeastern University},
    type   = {Doctoral dissertation},
    month  = jul,
    year   = {2025},
    pages  = {161}
  }
---

Performance and security are among the most desirable properties of Web Applications. The success of a Web Application depends on user satisfaction and is strongly correlated with the perceived responsiveness of the application and performance. Additionally, security is of utmost importance to retain user trust in a world ridden with malicious actors. However, drawing upon the full potential of a web application can involve the introduction of non-linear control flow, framework-specific changes and optimizations, or extensive refactoring for adoption of newer constructs in an ever-evolving ecosystem. Similarly, mitigating security vulnerabilities is also not trivial. These changes are often intrusive and can span multiple files. In this thesis, we explore how a declarative approach to specifying project-spanning program transformations can address these challenges.We present three major themes to improve the responsiveness and performance of web applications, and one theme to improve security: introducing asynchrony, introducing laziness, reducing superfluous computation, and introducing memory segmentation. We demonstrate the application of a declarative re-writing approach to these themes in the following contributions: (i) automatic migration from synchronous to asynchronous JavaScript APIs, (ii) increasing the responsiveness of web applications by introducing lazy loading, (iii) remediating superfluous re-rendering in React applications, and (iv) rewriting WebAssembly binaries to mitigate security vulnerabilities.