import { useTranslation } from 'react-i18next';
import { Globe, Check } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { languages, LanguageCode } from '../../i18n';

export function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentLanguage = languages.find((lang) => lang.code === i18n.language) || languages[0];

  const changeLanguage = (code: LanguageCode) => {
    i18n.changeLanguage(code);
    setIsOpen(false);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-md 
          bg-steel-900/50 border border-steel-800/50 
          hover:border-steel-700 hover:bg-steel-800/50 
          transition-all duration-150"
      >
        <Globe className="w-4 h-4 text-steel-400" />
        <span className="text-sm text-steel-300">{currentLanguage.flag}</span>
        <span className="text-xs text-steel-400 font-medium hidden sm:inline">
          {currentLanguage.name}
        </span>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          className="absolute right-0 mt-2 w-40 py-1 rounded-lg 
            bg-steel-900/95 backdrop-blur-xl border border-steel-800/50 
            shadow-lg shadow-navy-950/50 z-50
            animate-fade-in"
        >
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => changeLanguage(lang.code)}
              className={`
                w-full flex items-center justify-between px-3 py-2 
                text-sm transition-colors
                ${i18n.language === lang.code
                  ? 'text-electric bg-electric/5'
                  : 'text-steel-300 hover:text-text-primary hover:bg-steel-800/50'
                }
              `}
            >
              <div className="flex items-center gap-2">
                <span>{lang.flag}</span>
                <span>{lang.name}</span>
              </div>
              {i18n.language === lang.code && (
                <Check className="w-4 h-4 text-electric" />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
