import clsx from 'clsx';
import { TextareaHTMLAttributes, forwardRef, useEffect, useRef, useState, useCallback } from "react";

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  autoResize?: boolean;
  maxHeight?: number;
  useValidation?: boolean;
  validate?: (value: string) => { valid: boolean; errorMessage?: string };
  onValidatedChange?: (value: string) => void;
  updateOnBlur?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(({
  className,
  label,
  autoResize = false,
  maxHeight = 120, // default max height (roughly 5 lines)
  value: propValue,
  onChange,
  // New validation props
  useValidation = false,
  validate,
  onValidatedChange,
  updateOnBlur = false,
  onBlur,
  onKeyDown,
  ...props
}, ref) => {
  const internalRef = useRef<HTMLTextAreaElement>(null);
  const textareaRef = (ref as any) || internalRef;
  const adjustHeightTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Local state for validation mode
  const [localValue, setLocalValue] = useState(propValue as string);
  const [validationError, setValidationError] = useState<string | undefined>();
  const [isEditing, setIsEditing] = useState(false);

  // update local value when prop value changes
  useEffect(() => {
    setLocalValue(propValue as string);
  }, [propValue]);

  // Sync local state with prop value when not editing
  useEffect(() => {
    if (!isEditing) {
      setLocalValue(propValue as string);
    }
  }, [propValue, isEditing]);

  // Debounced adjustHeight function to prevent interference during rapid state changes
  const debouncedAdjustHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea || !autoResize) return;

    // Clear any pending timeout
    if (adjustHeightTimeoutRef.current) {
      clearTimeout(adjustHeightTimeoutRef.current);
    }

      // Debounce the height adjustment to prevent interference during rapid changes
      adjustHeightTimeoutRef.current = setTimeout(() => {
        // Re-check textarea reference (may have changed)
        const currentTextarea = textareaRef.current;
        if (!currentTextarea) return;
        
        // Check if textarea still exists and is mounted
        if (currentTextarea.offsetParent === null || !document.body.contains(currentTextarea)) {
          return;
        }
        
        // Store current focus state and selection
        let hadFocus = false;
        let selectionStart = 0;
        let selectionEnd = 0;
        
        // Safely get focus state and selection range (may fail if textarea is detached)
        try {
          hadFocus = document.activeElement === currentTextarea;
          if (hadFocus) {
            selectionStart = currentTextarea.selectionStart ?? 0;
            selectionEnd = currentTextarea.selectionEnd ?? 0;
          }
        } catch (e) {
          // If selection access fails, textarea may be detached, skip adjustment
          return;
        }
        
        // Prevent adjustment during focus events to avoid disruption
        requestAnimationFrame(() => {
          // Re-check textarea reference again (may have been unmounted)
          const textareaInFrame = textareaRef.current;
          if (!textareaInFrame) return;
          
          // Triple-check textarea still exists and is mounted before accessing it
          if (!document.body.contains(textareaInFrame) || textareaInFrame.offsetParent === null) {
            return;
          }
          
          try {
            // Verify textarea is still accessible
            if (typeof textareaInFrame.style === 'undefined' || 
                typeof textareaInFrame.scrollHeight === 'undefined') {
              return;
            }
            
            textareaInFrame.style.height = 'auto';
            const scrollHeight = textareaInFrame.scrollHeight;
            textareaInFrame.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
            
            // Add scrolling if content exceeds maxHeight
            textareaInFrame.style.overflowY = scrollHeight > maxHeight ? 'auto' : 'hidden';
            
            // Restore focus and selection if it was focused before
            if (hadFocus && document.activeElement !== textareaInFrame) {
              try {
                textareaInFrame.focus();
                // Safely restore selection (may fail if textarea is detached or in wrong state)
                if (typeof textareaInFrame.setSelectionRange === 'function') {
                  textareaInFrame.setSelectionRange(selectionStart, selectionEnd);
                }
              } catch (e) {
                // Ignore selection restoration errors if textarea is detached
              }
            }
          } catch (e) {
            // Ignore errors if textarea is no longer accessible
            // This can happen if component unmounts during animation frame
          }
        });
      }, 10); // Small debounce delay
  }, [autoResize, maxHeight, textareaRef]);

  useEffect(() => {
    debouncedAdjustHeight();
    
    // Add window resize listener
    window.addEventListener('resize', debouncedAdjustHeight);
    return () => {
      window.removeEventListener('resize', debouncedAdjustHeight);
      // Clear timeout on cleanup
      if (adjustHeightTimeoutRef.current) {
        clearTimeout(adjustHeightTimeoutRef.current);
      }
    };
  }, [localValue, debouncedAdjustHeight]);

  const validateAndUpdate = (value: string) => {
    if (validate) {
      const result = validate(value);
      setValidationError(result.errorMessage);
      if (result.valid && onValidatedChange) {
        onValidatedChange(value);
        return true;
      }
      return false;
    } else if (onValidatedChange) {
      onValidatedChange(value);
      return true;
    }
    return false;
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    setLocalValue(newValue);
    setIsEditing(true);

    if (!updateOnBlur) {
      if (useValidation) {
        validateAndUpdate(newValue);
      } else {
        onChange?.(e);
      }
    }
  };

  const handleBlur = (e: React.FocusEvent<HTMLTextAreaElement>) => {
    setIsEditing(false);
    if (updateOnBlur) {
      if (useValidation) {
        validateAndUpdate(localValue);
      } else {
        const syntheticEvent = {
          ...e,
          target: { ...e.target, value: localValue },
          currentTarget: { ...e.currentTarget, value: localValue }
        };
        onChange?.(syntheticEvent as any);
      }
    }
    onBlur?.(e);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (updateOnBlur && e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      textareaRef.current?.blur();
    }
    onKeyDown?.(e);
  };

  return (
    <div className="space-y-2">
      {label && (
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
      )}
      <textarea
        ref={textareaRef}
        onChange={handleChange}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        value={localValue}
        className={clsx(
          "flex w-full text-sm focus-visible:outline-none",
          "disabled:cursor-not-allowed disabled:opacity-50",
          "transition-colors",
          className
        )}
        style={{
          ...props.style,
          minHeight: autoResize ? '24px' : undefined,
        }}
        {...props}
      />
    </div>
  );
});

Textarea.displayName = "Textarea"; 