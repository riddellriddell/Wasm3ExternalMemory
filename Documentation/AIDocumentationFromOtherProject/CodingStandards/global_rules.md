version: 1.0
owner: "Jack Riddell"

# General Coding Principles
Your overarching goal is to produce code that is clean, efficient, and maintainable. You should always strive for readability, simplicity, and modularity, regardless of the programming language or context. Provide solutions in a supportive manner, ensuring that your recommendations are both actionable and adaptable. Avoid unnecessary complexity: keep your code open to iteration and future growth while preserving its clarity. Building upon these guiding principles, remember to respect language idioms, choose intuitive naming conventions, and consider best practices for error handling and testing from the outset. Whenever possible, aim for solutions that balance clarity with performance, factoring in future scalability and maintainability.

# General
- This is a public repository, so please be respectful of others and make sure the content makes sense to others.
- Clarity Over Brevity: Favor understandable code over clever tricks. Prioritize legibility and maintainability over saving a few lines.
- When fixing linting issues use the tools intended for this instead of trying to edit files yourself, directly.
- Adhere to the principle of DRY (Don't Repeat Yourself) when writing anything in this repository, code or text. Keep this in mind when reviewing files as well.
- Never say something without being certain. Always check your sources--after all you're free to look at the entire repository freely.
- Don't update documentation and description until after the behavior you're describing is actually saved into the repository.
- Always code in American English.
- Code should be understandable at a glance, making it more approachable for collaborators and your future self. Avoid obfuscation or over-optimization that sacrifices readability.
- Plan for growth and changing requirements, but do not overengineer. Keep your design flexible enough to adapt without complicating the initial implementation.
- Write straightforward code that conveys its intent clearly. Minimize abstraction layers that obscure readability.
- Use meaningful, consistent names for variables, functions, classes, and modules that reflect their purpose.
- Comment thoughtfull. Provide comments or docstrings where necessary, but avoid restating what the code already expresses.
- Encapsulate Complexity. Group related logic into self-contained modules or classes with clear, well-documented interfaces.
- Loose coupling. Design components to function independently, using abstraction layers or interfaces to reduce interdependencies.
- Adhere to SOLID principles.
- Apply DRY principles. Refactor repetitive or duplicated code into shared utilities or functions to promote reuse and reduce bloat.
-Design for Extensibility. Structure your codebase so you can add new features and functionalities without requiring major rewrites.

# Core System Components
- The main application logic is in source/.
- Feature flags and configuration settings are in source/config.
- Scripts are always in scripts/.
- Binary assets are always in resources/. (Examples of binary assets: image files such as .png, .jpg, .bmp, audio files such as .wav, .mp3, .ogg)


# Git
- Always write in American English.
- Small, focused PRs. No cross-cutting refactors with feature work.
- Commit prefix:
  - `Added:` feature name
  - `Fixed:` bug + file
  - `Changed:` refactor + subsystem
  - `Removed:` dead code
- Messages ≤72 chars subject
- Body mention each file changed and a summary of what the change was.
