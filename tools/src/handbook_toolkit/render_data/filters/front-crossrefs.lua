-- Cross-reference numbering policy for unnumbered front matter.
-- Run with:
--   filters:
--     - at: post-render
--       path: filters/front-crossrefs.lua
--
-- Ensures tables and figures in unnumbered front matter files receive continuous
-- 0.N labels (e.g. Table 0.1, Table 0.2) rather than disjoint per-page Table 1, 2, ...
-- counters, matching the canonical identifiers {#tbl-0-N} and {#fig-0-N}.

local function replace_number_inlines(inlines, n, prefix_word)
  for i = 1, #inlines do
    local span = inlines[i]
    local next_span = inlines[i + 1]
    local third_span = inlines[i + 2]

    -- Case 1: span is "Table" and next_span is space/nbsp, third_span is number or Span
    if span.tag == "Str" and span.text == prefix_word then
      if next_span and (next_span.tag == "Space" or (next_span.tag == "Str" and (next_span.text == " " or next_span.text == "\194\160"))) then
        if third_span then
          if third_span.tag == "Str" and third_span.text:match("^%d+") then
            if third_span.text:match("^0%.") then return true end
            local rest = third_span.text:gsub("^%d+", "")
            third_span.text = "0." .. n .. rest
            return true
          elseif third_span.tag == "Span" and #third_span.content > 0 then
            local inner = third_span.content[1]
            if inner.tag == "Str" and inner.text:match("^%d+") then
              if inner.text:match("^0%.") then return true end
              local rest = inner.text:gsub("^%d+", "")
              inner.text = "0." .. n .. rest
              return true
            end
          end
        end
      end
    end

    -- Case 2: span is "Table " or "Table " (prefix + space in one Str), next_span is number or Span
    if span.tag == "Str" and (span.text == prefix_word .. " " or span.text == prefix_word .. "\194\160" or span.text == prefix_word .. " ") then
      if next_span then
        if next_span.tag == "Str" and next_span.text:match("^%d+") then
          if next_span.text:match("^0%.") then return true end
          local rest = next_span.text:gsub("^%d+", "")
          next_span.text = "0." .. n .. rest
          return true
        elseif next_span.tag == "Span" and #next_span.content > 0 then
          local inner = next_span.content[1]
          if inner.tag == "Str" and inner.text:match("^%d+") then
            if inner.text:match("^0%.") then return true end
            local rest = inner.text:gsub("^%d+", "")
            inner.text = "0." .. n .. rest
            return true
          end
        end
      end
    end

    -- Case 3: span is "Table <num>" or "Table <num>" (all in one Str)
    if span.tag == "Str" and (span.text:match("^" .. prefix_word .. " %d+") or span.text:match("^" .. prefix_word .. "\194\160%d+") or span.text:match("^" .. prefix_word .. " %d+")) then
      if span.text:match("^" .. prefix_word .. "[%s\194\160 ]0%.") then return true end
      local sep = (span.text:match(" ") and " ") or (span.text:match("\194\160") and "\194\160") or " "
      local rest = span.text:gsub("^" .. prefix_word .. "[%s\194\160 ]%d+", "")
      span.text = prefix_word .. sep .. "0." .. n .. rest
      return true
    end
  end
  return false
end

function Div(el)
  local tbl_n = el.identifier:match("^tbl%-0%-(%d+)$")
  local fig_n = el.identifier:match("^fig%-0%-(%d+)$")

  -- GFM fallback: check if rawblock has div id
  if not (tbl_n or fig_n) then
    for _, b in ipairs(el.content) do
      if b.tag == "RawBlock" and b.text then
        tbl_n = b.text:match("tbl%-0%-(%d+)")
        fig_n = b.text:match("fig%-0%-(%d+)")
        if tbl_n or fig_n then break end
      end
    end
  end

  if tbl_n or fig_n then
    local n = tbl_n or fig_n
    local word = tbl_n and "Table" or "Figure"
    el = el:walk({
      Plain = function(p)
        replace_number_inlines(p.content, n, word)
        return p
      end,
      Para = function(p)
        replace_number_inlines(p.content, n, word)
        return p
      end
    })
  end
  return el
end

function Link(el)
  local tbl_n = el.target:match("tbl%-0%-(%d+)")
  local fig_n = el.target:match("fig%-0%-(%d+)")
  if tbl_n or fig_n then
    local n = tbl_n or fig_n
    local word = tbl_n and "Table" or "Figure"
    replace_number_inlines(el.content, n, word)
  end
  return el
end
