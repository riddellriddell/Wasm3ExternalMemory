Version: 1.0
Date Created: 5:49 PM 24/08/2025
Last Edit Date: 5:59 PM 24/08/2025
Owner: "Jarryd Adaens"

# WPF XAML Coding Rules (Workspace)

> Use in `.windsurf/rules` (e.g., `.windsurf/rules/wpf-xaml.md`) or manage globally via assistant memory. Targets WPF on .NET.

## Scope
- Applies to all XAML, code-behind, and view resources in this workspace.
- Goal: readable, MVVM-friendly, consistent markup with predictable runtime behavior.

## File & Project Layout
- One view per file (`Window`, `UserControl`, `DataTemplate` in `*.xaml` with partial class in `*.xaml.cs`).
- Keep resource dictionaries in `/Resources` (global) and `/Themes` for control libraries. Use `MergedDictionaries` for composition.
- Public styles/templates live at App or Window scope; private styles local to the view.

## Names, Namescopes, and Identifiers
- Use `Name` for `FrameworkElement` descendants. Use `x:Name` when the type has no `Name` property (e.g., animations, brushes, templates).
- Names must be unique per XAML namescope. Prefer stable, descriptive names (`CustomerList`, `SaveButton`). Avoid Hungarian.  
- Avoid naming elements that are not referenced by binding, animation, or code-behind.

## Dependency Properties & Routed Events
- Custom DP field: `<PropertyName>Property`, static `readonly DependencyProperty`, registered via `DependencyProperty.Register`. CLR wrapper is:
  ```csharp
  public T PropertyName
  {
      get => (T)GetValue(PropertyNameProperty);
      set => SetValue(PropertyNameProperty, value);
  }
  ```
- Supply metadata when behavior affects layout/measure (`AffectsRender`, `AffectsMeasure`) or needs callbacks (use `FrameworkPropertyMetadata`).
- Prefer routed events for UI interactions that must bubble/tunnel across the tree. Use standard naming (`<Verb><Noun>`), and mark handled when appropriate.

## Binding & MVVM
- Set `DataContext` at the view root. No `ElementName` hops for app data unless necessary.
- Use `{Binding Property}` form; omit `Path=` when simple. Explicit `Mode` only when different from default.
- `TextBox.Text`: leave `UpdateSourceTrigger=LostFocus` unless you need real-time updates. Use `PropertyChanged` only when required.
- Use `ICommand` for actions. No click-handlers for business logic in code-behind.
- For templated bindings, prefer `TemplateBinding` or `RelativeSource TemplatedParent` where appropriate.
- Use converters sparingly. Prefer view-model projection properties over complex converter graphs.

## Resources, Styles, and Templates
- Default to `{StaticResource}`. Use `{DynamicResource}` only when a value must change at runtime (theming, live palette).
- No forward references with `{StaticResource}`. Define resources before use. If unavoidable, consider `{DynamicResource}`.
- Use implicit styles for control-wide defaults; explicit styles for targets that need variations. Use `BasedOn` for inheritance.
- Keep visual states and triggers inside control templates. Avoid heavy triggers for simple value transforms; use bindings or visual states.

## Layout & Controls
- Favor `Grid` for non-trivial layouts; name rows/columns in comments. Avoid deep nesting of `StackPanel` and `Grid`.
- Use `ItemsControl`/`ListBox`/`ListView` with virtualization where possible. Prefer recycling mode:
  - `VirtualizingPanel.IsVirtualizing="True"`
  - `VirtualizingPanel.VirtualizationMode="Recycling"`
  - `ScrollViewer.CanContentScroll="True"`
  - Consider `VirtualizingPanel.IsVirtualizingWhenGrouping="True"` when grouping.
- Keep `Margin` on child elements; avoid setting `Margin` on containers when it leaks into unrelated children.

## Formatting Rules (Enforced)
- Indentation: 2 spaces. No tabs in XAML.
- One element per line. Self-close empty elements (`<Separator />`).
- Attribute layout:
  - Short elements: keep on one line if under ~120 chars.
  - Otherwise: start tag on one line, attributes each on their own line, closing `>` on a new line.
- Namespace order: `x:Class`, then `xmlns`, `xmlns:x`, then other `xmlns:*`.
- Attribute order uses XAML Styler defaults (see below). Keep key identity attrs first (`x:Key`, `x:Name`/`Name`, `x:Uid`).

## XAML Styler Baseline (Attribute Order)
Use these groups to auto-order attributes (top→bottom; inside group left→right):

1) `x:Class`  
2) `xmlns, xmlns:x`  
3) `xmlns:*`  
4) `x:Key, Key, x:Name, Name, x:Uid, Uid, Title`  
5) `Grid.Row, Grid.RowSpan, Grid.Column, Grid.ColumnSpan, Canvas.Left, Canvas.Top, Canvas.Right, Canvas.Bottom`  
6) `Width, Height, MinWidth, MinHeight, MaxWidth, MaxHeight`  
7) `Margin, Padding, HorizontalAlignment, VerticalAlignment, HorizontalContentAlignment, VerticalContentAlignment, Panel.ZIndex`  
8) `*:* , *`  
9) `PageSource, PageIndex, Offset, Color, TargetName, Property, Value, StartPoint, EndPoint`  
10) `mc:Ignorable, d:IsDataSource, d:LayoutOverrides, d:IsStaticText`  
11) `Storyboard.*, From, To, Duration`

## Code-Behind
- Keep code-behind minimal: view plumbing only (attached behaviors, minor UI glue). No business logic.
- Use `partial` class with same root type. Event handlers should delegate to commands when possible.

## Comments & Docs
- Short `<!-- ... -->` comments above complex elements or groups. Avoid trailing comments on attribute lines.
- Document non-obvious bindings, converters, and triggers.

## Tooling

- Use XAML Styler (or equivalent) with the attribute order above. Run on save and in CI.
- Add analyzers for dead bindings and missing resources where available (e.g., WpfAnalyzers).
- Use Live Visual Tree/Live Property Explorer and Snoop for runtime inspection.

## Examples

### Resource dictionary
```xml
<ResourceDictionary
  xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
  xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
  xmlns:conv="clr-namespace:App.Converters">
  <SolidColorBrush x:Key="PrimaryBrush" Color="#1F6FEB" />
  <conv:BooleanToVisibilityConverter x:Key="BoolToVis" />
  <Style TargetType="Button" x:Key="PrimaryButton" BasedOn="{StaticResource {x:Type Button}}">
    <Setter Property="Foreground" Value="White" />
    <Setter Property="Background" Value="{StaticResource PrimaryBrush}" />
  </Style>
</ResourceDictionary>
```

### UserControl view
```xml
<UserControl
  x:Class="App.Views.CustomerView"
  xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
  xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
  xmlns:d="http://schemas.microsoft.com/expression/blend/2008"
  xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
  xmlns:vm="clr-namespace:App.ViewModels"
  mc:Ignorable="d">
  <UserControl.DataContext>
    <vm:CustomerViewModel />
  </UserControl.DataContext>

  <Grid>
    <Grid.RowDefinitions>
      <RowDefinition Height="Auto" />
      <RowDefinition Height="*" />
    </Grid.RowDefinitions>

    <TextBox
      Grid.Row="0"
      Name="SearchBox"
      Text="{Binding Query, UpdateSourceTrigger=LostFocus}"
      Margin="0,0,0,8"
      AutomationProperties.Name="Search" />

    <ListBox
      Grid.Row="1"
      ItemsSource="{Binding Results}"
      VirtualizingPanel.IsVirtualizing="True"
      VirtualizingPanel.VirtualizationMode="Recycling"
      ScrollViewer.CanContentScroll="True">
      <ListBox.ItemTemplate>
        <DataTemplate>
          <TextBlock Text="{Binding FullName}" />
        </DataTemplate>
      </ListBox.ItemTemplate>
    </ListBox>
  </Grid>
</UserControl>
```

## Do Not

- Don’t use {DynamicResource} unless runtime changes are required.
- Don’t set DataContext deep in the tree without reason.
- Don’t put business logic in code-behind.
- Don’t forward-reference resources with {StaticResource}.
- Don’t disable virtualization on large lists; prefer recycling mode and `CanContentScroll="True"`.
